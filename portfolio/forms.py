from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import ClientLead


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
