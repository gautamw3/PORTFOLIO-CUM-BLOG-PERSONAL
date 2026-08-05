from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from portfolio_cum_blog import settings

from .models import ClientLead, ReviewCampaign, UserSkill


def normalize_phone_number(phone_value, default_country_code=""):
    """Convert a raw phone number into a basic E.164-like value."""
    raw_value = (phone_value or "").strip()
    digits = "".join(character for character in raw_value if character.isdigit())
    if raw_value.startswith("+") and digits:
        return f"+{digits}"
    if raw_value.startswith("00") and len(digits) > 2:
        return f"+{digits[2:]}"
    if len(digits) == 10 and default_country_code:
        country_digits = "".join(
            character for character in default_country_code if character.isdigit()
        )
        if country_digits:
            return f"+{country_digits}{digits}"
    if digits:
        return f"+{digits}"
    return ""


def normalize_country_code(country_code_value):
    """Normalize country code to +<digits> format."""
    raw_value = (country_code_value or "").strip()
    digits = "".join(character for character in raw_value if character.isdigit())
    if not digits:
        return ""
    return f"+{digits}"


class ContactUs(forms.ModelForm):
    message = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = ClientLead
        fields = [  # noqa: RUF012
            "client_name",
            "client_email",
            "subject",
            "message",
            "file_supporting_the_message",
        ]
        widgets = {  # noqa: RUF012
            "client_name": forms.TextInput(attrs={"placeholder": "Your name"}),
            "client_email": forms.TextInput(attrs={"placeholder": "Your email"}),
            "subject": forms.TextInput(attrs={"placeholder": "Subject line"}),
        }
        labels = {  # noqa: RUF012
            "client_name": "Name",
            "client_email": "Email",
            "subject": "Subject",
            "message": "Message",
            "file_supporting_the_message": "Supporting File",
        }
        help_texts = {  # noqa: RUF012
            "message": "",
        }


class ReviewSubmissionForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput(), required=False)
    reviewer_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"placeholder": "Your name", "class": "form-control"}
        ),
    )
    reviewer_rating = forms.ChoiceField(
        choices=UserSkill.STAR_RATINGS,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    review_description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "Tell us about your experience",
                "rows": 5,
                "class": "form-control",
            }
        )
    )


class ReviewInvitationBulkForm(forms.Form):
    campaign = forms.ModelChoiceField(
        queryset=ReviewCampaign.objects.none(),
        empty_label="Select active campaign",
        help_text="Only active campaigns are shown here.",
    )
    message_body = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": "vLargeTextField",
                "placeholder": (
                    "Hi {name}, thank you for choosing us. Please tap {link} "
                    "to share your review."
                ),
            }
        )
    )
    recipients = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 8,
                "class": "vLargeTextField",
                "placeholder": "Name, +1234567890\n+1234567891",
            }
        ),
        help_text=(
            "Enter one recipient per line. Use 'Name, Phone' or just the phone "
            "number."
        ),
    )
    default_country_code = forms.CharField(
        max_length=8,
        required=False,
        initial=getattr(settings, "REVIEW_INVITATION_DEFAULT_COUNTRY_CODE", "+91"),
        widget=forms.TextInput(
            attrs={"placeholder": "+91", "class": "vTextField"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campaign"].queryset = ReviewCampaign.objects.filter(
            is_active=True
        ).order_by("name")

    def clean_recipients(self):
        raw_recipients = self.cleaned_data["recipients"].splitlines()
        # recipients is validated before default_country_code, so read both sources safely
        default_country_code = normalize_country_code(
            self.cleaned_data.get("default_country_code")
            or self.data.get("default_country_code")
        )
        parsed_recipients = []

        for line_number, raw_recipient in enumerate(raw_recipients, start=1):
            cleaned_line = raw_recipient.strip()
            if not cleaned_line:
                continue

            recipient_name = ""
            recipient_phone = cleaned_line
            for separator in (",", "|", ";"):
                if separator in cleaned_line:
                    first_part, second_part = cleaned_line.split(separator, 1)
                    recipient_name = first_part.strip()
                    recipient_phone = second_part.strip()
                    break

            normalized_phone = normalize_phone_number(
                recipient_phone, default_country_code=default_country_code
            )
            if not normalized_phone:
                raise forms.ValidationError(
                    f"Line {line_number} does not contain a valid phone number."
                )

            parsed_recipients.append(
                {
                    "recipient_name": recipient_name,
                    "recipient_phone": normalized_phone,
                }
            )

        if not parsed_recipients:
            raise forms.ValidationError("Add at least one recipient to continue.")

        return parsed_recipients
