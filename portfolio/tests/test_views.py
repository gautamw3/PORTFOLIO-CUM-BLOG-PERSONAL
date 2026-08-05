import json
from datetime import date
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from portfolio import views
from portfolio.models import (
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


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def rendered(monkeypatch):
    def _render(request, template, context):
        return {"template": template, "context": context}

    monkeypatch.setattr(views, "render", _render)


@pytest.fixture
def data_setup(db, monkeypatch):
    user = User.objects.create_user(
        username="base-user",
        email="base@example.com",
        password="base-pass",
        first_name="Base",
        last_name="User",
    )
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    portfolio_user = PortfolioUser.objects.create(
        user=user,
        role="Developer",
        profile_short_description="Short profile",
        mobile="1234567890",
        heading="Hello",
        headline="Building web products",
        about="About content",
        profile_photo="portfolio/profile_photo/base.jpg",
        work_days="1",
        work_shift="1",
        is_blogger=True,
    )
    PortfolioUserAddress.objects.create(
        user=portfolio_user,
        country="India",
        state="Karnataka",
        city="Bengaluru",
    )
    PortfolioUserSocialMediaLink.objects.create(
        user=portfolio_user,
        github="https://github.com/base",
        linkedin="https://linkedin.com/in/base",
        tweeter="https://twitter.com/base",
        instagram="https://instagram.com/base",
    )
    skill_category = SkillCategory.objects.create(category_name="PLBE")
    skill = Skill.objects.create(
        skill_category=skill_category,
        category_item_name="Python",
        category_item_image="portfolio/skill_images/python.png",
    )
    user_skill = UserSkill.objects.create(
        user=user,
        skill_category=skill_category,
        skill=skill,
        summary="Experienced in Python",
        description="Python description",
        rating_out_of_five="4",
        total_experience_in_year="5",
        last_used=date(2025, 1, 1),
    )
    Review.objects.create(
        reviewer_name="Jane",
        reviewer_rating="5",
        review_description="Great work",
        is_approved=True,
    )
    Resume.objects.create(
        user=portfolio_user,
        resume_file="portfolio/resume/base_resume.pdf",
    )
    project = ClientProject.objects.create(
        user=portfolio_user,
        project_title="Project A",
        client_name="Client A",
        project_url="https://example.com/project-a",
        project_description="Project description",
    )
    project.tools_and_technologies_used.set([user_skill])

    monkeypatch.setattr(views.settings, "DEFAULT_USER", user.id)

    return SimpleNamespace(
        user=user,
        portfolio_user=portfolio_user,
        skill=skill,
        user_skill=user_skill,
    )


@pytest.mark.django_db
def test_helper_functions(data_setup):
    response_obj = views.get_global_response(None)
    assert {"response", "responseMessage", "responseMessageInfo"} == set(response_obj)

    user = views.get_global_user(None)
    assert user.id == data_setup.user.id

    skills = views.get_user_skills(data_setup.user.id)
    assert isinstance(skills, dict)
    assert "Programming languages" in skills

    reviews = views.get_customer_reviews()
    assert len(reviews) >= 1


@pytest.mark.django_db
def test_get_social_media_links_branches(data_setup):
    existing = views.get_social_media_links(data_setup.portfolio_user.id)
    assert existing is not None

    missing = views.get_social_media_links(999999)
    assert missing is None

    PortfolioUserSocialMediaLink.objects.create(
        user=data_setup.portfolio_user,
        github="https://github.com/base2",
        linkedin="https://linkedin.com/in/base2",
        tweeter="https://twitter.com/base2",
        instagram="https://instagram.com/base2",
    )
    multiple = views.get_social_media_links(data_setup.portfolio_user.id)
    assert multiple is not None


@pytest.mark.django_db
def test_index_authenticated_success(rf, rendered, data_setup):
    request = rf.get("/")
    request.user = data_setup.user

    result = views.index(request)
    assert result["template"] == "portfolio/index.html"
    assert result["context"]["page_title"] == "Home"
    assert result["context"]["email"] == data_setup.user.email


@pytest.mark.django_db
def test_index_exception_branch(rf, rendered, monkeypatch, data_setup):
    request = rf.get("/")
    request.user = data_setup.user

    monkeypatch.setattr(
        views.User.objects,
        "get",
        lambda **kwargs: (_ for _ in ()).throw(TypeError("boom")),
    )

    result = views.index(request)
    assert result["context"]["page_title"] == "Home"
    assert "exception" in result["context"]


@pytest.mark.django_db
def test_tech_details_success_and_invalid_method(rf, rendered, data_setup):
    request = rf.get(f"/tech_details/{data_setup.skill.id}")
    request.user = data_setup.user

    success = views.tech_details(request, data_setup.skill.id)
    assert success["template"] == "portfolio/tech_details.html"
    assert success["context"]["page_details"]["breadcrumb_mid_item"] == "Python"

    invalid_request = rf.post(f"/tech_details/{data_setup.skill.id}")
    invalid_request.user = data_setup.user
    invalid = views.tech_details(invalid_request, data_setup.skill.id)
    assert "error" in invalid["context"]


@pytest.mark.django_db
def test_tech_details_not_found(rf, rendered, data_setup):
    request = rf.get("/tech_details/999999")
    request.user = data_setup.user

    result = views.tech_details(request, 999999)
    assert result["context"]["page_details"] is None
    assert "exception" in result["context"]


@pytest.mark.django_db
def test_new_client_feed_branches(rf):
    success_req = rf.post("/new_client_feed/", {"new_client_email": "new@example.com"})
    success_payload = json.loads(views.new_client_feed(success_req).content.decode())
    assert success_payload["response"] == "success"
    assert NewClient.objects.filter(client_email="new@example.com").exists()

    missing_req = rf.post("/new_client_feed/", {})
    missing_payload = json.loads(views.new_client_feed(missing_req).content.decode())
    assert missing_payload["response"] == "error"

    method_payload = json.loads(
        views.new_client_feed(rf.get("/new_client_feed/")).content.decode()
    )
    assert method_payload["response"] == "error"


@pytest.mark.django_db
def test_send_new_client_lead_mail(monkeypatch):
    class DummyTemplate:
        def render(self, data):
            return "rendered-body"

    sent = {}

    class DummyEmail:
        def __init__(self, subject, body, from_email, to, reply_to=None):
            sent["subject"] = subject
            sent["body"] = body
            sent["to"] = to
            sent["reply_to"] = reply_to
            self.content_subtype = ""

        def send(self, fail_silently=False):
            sent["sent"] = True

    monkeypatch.setattr(views, "get_template", lambda template: DummyTemplate())
    monkeypatch.setattr(views, "EmailMessage", DummyEmail)

    views.send_new_client_lead_mail({"client_email": "lead@example.com"})
    assert sent["sent"] is True
    assert sent["to"] == ["lead@example.com"]


@pytest.mark.django_db
def test_contact_us_get_and_post(rf, rendered, monkeypatch, data_setup):
    monkeypatch.setattr(views, "send_new_client_lead_mail", lambda email_data: None)

    get_request = rf.get("/contact_us/")
    get_request.user = data_setup.user
    get_result = views.contact_us(get_request)
    assert get_result["template"] == "portfolio/contact_us.html"
    assert get_result["context"]["page_title"] == "Contact us"

    post_request = rf.post(
        "/contact_us/",
        {
            "client_name": "Client",
            "client_email": "client@example.com",
            "subject": "Need help",
            "message": "Please contact me",
        },
    )
    post_request.user = data_setup.user
    post_result = views.contact_us(post_request)
    assert post_result["context"]["response"] in {"success", "error"}


@pytest.mark.django_db
def test_about_me_and_user_portfolio(rf, rendered, data_setup):
    about_request = rf.get("/about_me/")
    about_request.user = data_setup.user
    about_result = views.about_me(about_request)
    assert about_result["template"] == "portfolio/about-me.html"

    about_invalid_request = rf.post("/about_me/")
    about_invalid_request.user = data_setup.user
    about_invalid_result = views.about_me(about_invalid_request)
    assert "error" in about_invalid_result["context"]

    portfolio_request = rf.get("/user_portfolio/")
    portfolio_request.user = data_setup.user
    portfolio_result = views.user_portfolio(portfolio_request)
    assert portfolio_result["template"] == "portfolio/portfolio.html"


@pytest.mark.django_db
def test_user_profile_details_branches(rf, rendered, data_setup):
    success_request = rf.get(f"/user_profile_details/{data_setup.user.id}")
    success_request.user = data_setup.user
    success = views.user_profile_details(success_request, data_setup.user.id)
    assert success["template"] == "portfolio/profile_details.html"
    assert success["context"]["user_first_name"] == data_setup.user.first_name

    invalid_request = rf.post(f"/user_profile_details/{data_setup.user.id}")
    invalid_request.user = data_setup.user
    invalid = views.user_profile_details(invalid_request, data_setup.user.id)
    assert "error" in invalid["context"]

    missing_request = rf.get("/user_profile_details/999999")
    missing_request.user = data_setup.user
    missing = views.user_profile_details(missing_request, 999999)
    assert "exception" in missing["context"]


@pytest.mark.django_db
def test_get_global_user_with_anonymous_request(rf, rendered, data_setup):
    request = rf.get("/")
    request.user = AnonymousUser()

    result = views.index(request)
    assert result["template"] == "portfolio/index.html"


@pytest.mark.django_db
def test_write_review_view_get_and_post(rf, rendered, data_setup):
    campaign = ReviewCampaign.objects.create(
        name="SMS Campaign",
        message_template="Hi {name}, please review: {link}",
        created_by=data_setup.user,
    )
    invitation = ReviewInvitation.objects.create(
        campaign=campaign,
        recipient_name="Jane",
        recipient_phone="+15555550123",
    )

    get_request = rf.get(f"/write-review/?token={invitation.token}")
    get_request.user = data_setup.user
    get_result = views.write_review(get_request)
    assert get_result["template"] == "portfolio/write_review.html"
    assert get_result["context"]["review_invitation"].id == invitation.id

    post_request = rf.post(
        "/write-review/",
        {
            "token": str(invitation.token),
            "reviewer_name": "Jane Doe",
            "reviewer_rating": "5",
            "review_description": "Great experience.",
        },
    )
    post_request.user = data_setup.user
    post_result = views.write_review(post_request)
    assert post_result["context"]["response"] == "success"
    invitation.refresh_from_db()
    assert invitation.sms_status == "reviewed"
    assert invitation.review is not None
