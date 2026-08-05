import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from portfolio.models import Review, ReviewCampaign, ReviewInvitation


@pytest.mark.django_db
def test_review_campaign_admin_has_send_invitation_link(client):
    admin_user = User.objects.create_superuser(
        username="admin-user",
        email="admin@example.com",
        password="admin-pass",
    )
    client.force_login(admin_user)

    response = client.get(reverse("admin:portfolio_reviewcampaign_changelist"))

    assert response.status_code == 200
    assert b"Send Review Invitation" in response.content


@pytest.mark.django_db
def test_review_campaign_admin_bulk_send_creates_campaign_and_invitations(
    client, monkeypatch
):
    admin_user = User.objects.create_superuser(
        username="admin-user-2",
        email="admin2@example.com",
        password="admin-pass",
    )
    client.force_login(admin_user)

    campaign = ReviewCampaign.objects.create(
        name="Admin Review Outreach",
        is_active=True,
        message_template="Hi {name}, please share a review: {link}",
        created_by=admin_user,
    )

    monkeypatch.setattr(
        "portfolio.admin.send_review_sms",
        lambda phone_number, message_body: {"MessageId": f"msg-{phone_number[-4:]}"},
    )

    response = client.post(
        reverse("admin:portfolio_reviewcampaign_send_review_invitation"),
        {
            "campaign": campaign.id,
            "message_body": "Hi {name}, please share a review: {link}",
            "recipients": "Alex, 5550001111\n5550002222",
            "default_country_code": "+1",
        },
        follow=True,
    )

    assert response.status_code == 200
    campaign.refresh_from_db()
    invitations = ReviewInvitation.objects.filter(campaign=campaign).order_by("id")
    assert campaign.sent_count == 2
    assert invitations.count() == 2
    assert invitations.filter(sms_status="sent").count() == 2
    assert invitations[0].recipient_phone == "+15550001111"
    assert invitations[1].recipient_phone == "+15550002222"


@pytest.mark.django_db
def test_frontend_shows_only_approved_reviews(rf):
    from portfolio import views

    Review.objects.create(
        reviewer_name="Approved",
        reviewer_rating="5",
        review_description="Visible review",
        is_approved=True,
    )
    Review.objects.create(
        reviewer_name="Pending",
        reviewer_rating="4",
        review_description="Hidden review",
        is_approved=False,
    )

    reviews = views.get_customer_reviews()
    reviewers = {item["reviewer"] for item in reviews}

    assert "Approved" in reviewers
    assert "Pending" not in reviewers


@pytest.mark.django_db
def test_review_detail_approval_sets_approver_and_time(client):
    admin_user = User.objects.create_superuser(
        username="admin-review-approver",
        email="admin-approver@example.com",
        password="admin-pass",
    )
    client.force_login(admin_user)

    review = Review.objects.create(
        reviewer_name="Needs Approval",
        reviewer_rating="4",
        review_description="Please approve this.",
        is_approved=False,
    )

    change_url = reverse("admin:portfolio_review_change", args=[review.id])
    response = client.post(
        change_url,
        {
            "reviewer_name": review.reviewer_name,
            "reviewer_rating": review.reviewer_rating,
            "review_description": review.review_description,
            "is_approved": "on",
            "_save": "Save",
        },
        follow=True,
    )

    assert response.status_code == 200
    review.refresh_from_db()
    assert review.is_approved is True
    assert review.approved_by == admin_user
    assert review.approved_at is not None
