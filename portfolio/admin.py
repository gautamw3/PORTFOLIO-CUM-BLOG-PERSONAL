from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from portfolio_cum_blog import settings

from .forms import ReviewInvitationBulkForm
from .review_services import build_review_message, send_review_sms

from .models import (
    ClientLead,
    ClientProject,
    NewClient,
    PortfolioUser,
    PortfolioUserAddress,
    PortfolioUserSocialMediaLink,
    Resume,
    Review,
    ReviewCampaign,
    ReviewInvitation,
    Skill,
    SkillCategory,
    UserSkill,
)

# Register your models here.

admin.site.register(PortfolioUser)
admin.site.register(SkillCategory)
admin.site.register(Skill)
admin.site.register(UserSkill)
admin.site.register(PortfolioUserSocialMediaLink)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "reviewer_name",
        "reviewer_rating",
        "is_approved",
        "approved_by",
        "approved_at",
        "created_at",
    )
    list_filter = ("is_approved", "reviewer_rating")
    search_fields = ("reviewer_name", "review_description")
    readonly_fields = ("approved_by", "approved_at", "created_at", "updated_at")
    actions = ("approve_reviews", "unapprove_reviews")

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        now = timezone.now()
        queryset.update(is_approved=True, approved_by=request.user, approved_at=now)

    @admin.action(description="Unapprove selected reviews")
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False, approved_by=None, approved_at=None)

    def save_model(self, request, obj, form, change):
        """Keep approval audit fields in sync for detail-page edits."""
        if obj.is_approved:
            if obj.approved_at is None:
                obj.approved_at = timezone.now()
            if obj.approved_by is None:
                obj.approved_by = request.user
        else:
            obj.approved_at = None
            obj.approved_by = None
        super().save_model(request, obj, form, change)


admin.site.register(NewClient)
admin.site.register(PortfolioUserAddress)
admin.site.register(ClientLead)
admin.site.register(ClientProject)
admin.site.register(Resume)


class ReviewInvitationInline(admin.TabularInline):
    model = ReviewInvitation
    extra = 0
    can_delete = False
    fields = (
        "recipient_name",
        "recipient_phone",
        "sms_status",
        "review_url",
        "review",
        "reviewed_at",
        "sent_at",
        "sms_error",
    )
    readonly_fields = fields
    show_change_link = True


@admin.register(ReviewCampaign)
class ReviewCampaignAdmin(admin.ModelAdmin):
    change_list_template = "admin/portfolio/reviewcampaign/change_list.html"
    inlines = (ReviewInvitationInline,)
    list_display = (
        "name",
        "is_active",
        "sender_id",
        "sent_count",
        "failed_count",
        "submitted_count",
        "created_at",
    )
    search_fields = ("name", "sender_id")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
    readonly_fields = ("sent_count", "failed_count", "created_at", "updated_at")

    def submitted_count(self, obj):
        return obj.invitations.filter(review__isnull=False).count()

    submitted_count.short_description = "Submitted"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "send-review-invitation/",
                self.admin_site.admin_view(self.send_review_invitation_view),
                name="portfolio_reviewcampaign_send_review_invitation",
            ),
        ]
        return custom_urls + urls

    def send_review_invitation_view(self, request):
        form = ReviewInvitationBulkForm(request.POST or None)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Send Review Invitation",
            "form": form,
            "has_active_campaigns": form.fields["campaign"].queryset.exists(),
        }

        if request.method == "POST":
            if form.is_valid():
                campaign = form.cleaned_data["campaign"]
                campaign.message_template = form.cleaned_data["message_body"].strip()
                campaign.sender_id = getattr(
                    settings, "AWS_EUM_ORIGINATION_IDENTITY", ""
                )
                campaign.save(
                    update_fields=["message_template", "sender_id", "updated_at"]
                )

                sent_count = 0
                failed_count = 0
                for recipient in form.cleaned_data["recipients"]:
                    invitation = ReviewInvitation.objects.create(
                        campaign=campaign,
                        recipient_name=recipient["recipient_name"],
                        recipient_phone=recipient["recipient_phone"],
                    )

                    review_path = reverse("write_review")
                    review_link = request.build_absolute_uri(
                        f"{review_path}?token={invitation.token}"
                    )
                    invitation.review_url = review_link
                    invitation.save(update_fields=["review_url", "updated_at"])

                    message_body = build_review_message(
                        campaign.message_template,
                        review_link,
                        recipient_name=recipient["recipient_name"],
                    )
                    try:
                        sms_response = send_review_sms(
                            invitation.recipient_phone,
                            message_body,
                        )
                        invitation.sms_message_id = sms_response.get("MessageId", "")
                        invitation.sms_status = "sent"
                        invitation.sent_at = timezone.now()
                        invitation.sms_error = ""
                        invitation.save(
                            update_fields=[
                                "sms_message_id",
                                "sms_status",
                                "sent_at",
                                "sms_error",
                                "updated_at",
                            ]
                        )
                        sent_count += 1
                    except Exception as err:  # noqa: BLE001
                        invitation.sms_status = "failed"
                        invitation.sms_error = str(err)
                        invitation.save(
                            update_fields=["sms_status", "sms_error", "updated_at"]
                        )
                        failed_count += 1

                campaign.sent_count += sent_count
                campaign.failed_count += failed_count
                campaign.save(
                    update_fields=["sent_count", "failed_count", "updated_at"]
                )
                self.message_user(
                    request,
                    f"Campaign processed. Sent: {sent_count}, Failed: {failed_count}.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(
                    reverse(
                        "admin:portfolio_reviewcampaign_change",
                        args=[campaign.id],
                    )
                )

            self.message_user(
                request,
                "Please correct the highlighted form errors.",
                level=messages.ERROR,
            )

        return TemplateResponse(
            request,
            "admin/portfolio/reviewcampaign/send_review_invitation.html",
            context,
        )
