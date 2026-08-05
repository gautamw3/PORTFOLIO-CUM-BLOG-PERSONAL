import importlib

from portfolio.constants import SUB_CLIENT_LEAD_EMAIL
from portfolio.forms import ContactUs, ReviewInvitationBulkForm, ReviewSubmissionForm
from portfolio import urls as portfolio_urls
from portfolio_cum_blog import asgi, storage_backends, urls, wsgi


def test_constants_are_defined():
    assert "Greetings" in SUB_CLIENT_LEAD_EMAIL


def test_contact_form_has_expected_fields():
    form = ContactUs()
    assert "client_name" in form.fields
    assert "client_email" in form.fields
    assert "subject" in form.fields
    assert "message" in form.fields


def test_review_forms_have_expected_fields():
    submission_form = ReviewSubmissionForm()
    assert "reviewer_name" in submission_form.fields
    assert "reviewer_rating" in submission_form.fields
    assert "review_description" in submission_form.fields

    bulk_form = ReviewInvitationBulkForm()
    assert "campaign" in bulk_form.fields
    assert "message_body" in bulk_form.fields
    assert "recipients" in bulk_form.fields


def test_portfolio_urls_reverse_resolution():
    names = {
        getattr(pattern, "name", None)
        for pattern in portfolio_urls.urlpatterns
        if getattr(pattern, "name", None)
    }
    assert "index" in names
    assert "write_review" in names


def test_project_urls_are_loaded():
    assert len(urls.urlpatterns) > 0


def test_storage_backend_configuration():
    assert storage_backends.StaticStorage.location == "static"
    assert storage_backends.MediaStorage.location == "media"
    assert storage_backends.MediaStorage.file_overwrite is False


def test_asgi_and_wsgi_application_objects_exist():
    assert asgi.application is not None
    assert wsgi.application is not None


def test_manage_main_executes_command(monkeypatch):
    manage_module = importlib.import_module("manage")
    called = {}

    def fake_exec(argv):
        called["argv"] = argv

    monkeypatch.setattr("django.core.management.execute_from_command_line", fake_exec)
    monkeypatch.setattr(manage_module.sys, "argv", ["manage.py", "check"])

    manage_module.main()
    assert called["argv"][1] == "check"
