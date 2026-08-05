import pytest
from django.contrib.auth.models import User

from portfolio.models import (
    ClientLead,
    ClientProject,
    NewClient,
    PortfolioUser,
    PortfolioUserAddress,
    PortfolioUserSocialMediaLink,
    ReviewCampaign,
    ReviewInvitation,
    Review,
    Skill,
    SkillCategory,
    UserSkill,
)


@pytest.mark.django_db
def test_create_portfolio_user():
    user = User.objects.create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email="someone@abc.com",
    )
    portfolio_user = PortfolioUser.objects.create(
        user=user,
        role="Developer",
        profile_short_description="Short description",
        mobile="1234567890",
        heading="Test Heading",
        headline="Test Headline",
        about="This is a test about section.",
        profile_photo="path/to/photo.jpg",
        work_days="1",
        work_shift="1",
        is_blogger=True,
    )
    assert portfolio_user.user == user


@pytest.mark.django_db
def test_create_portfolio_user_address():
    user = User.objects.create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email="someone@abc.com",
    )
    portfolio_user = PortfolioUser.objects.create(
        user=user,
        role="Developer",
        profile_short_description="Short description",
        mobile="1234567890",
        heading="Test Heading",
        headline="Test Headline",
        about="This is a test about section.",
        profile_photo="path/to/photo.jpg",
        work_days="1",
        work_shift="1",
    )
    address = PortfolioUserAddress.objects.create(
        user_id=portfolio_user.user.id,
        country="India",
        state="Karnataka",
        city="Bangalore",
    )
    assert address.country == "India"
    assert address.state == "Karnataka"
    assert address.city == "Bangalore"


@pytest.mark.django_db
def test_portfolio_user_social_links():
    user = User.objects.create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email="someone@example.com",
    )
    portfolio_user = PortfolioUser.objects.create(
        user=user,
        role="Developer",
        profile_short_description="Short description",
        mobile="1234567890",
        heading="Test Heading",
        headline="Test Headline",
        about="This is a test about section.",
        profile_photo="path/to/photo.jpg",
        work_days="1",
        work_shift="1",
    )
    social_links = PortfolioUserSocialMediaLink.objects.create(
        user=portfolio_user,
        github="abc@github.com",
        linkedin="abc.linkedin.com",
        tweeter="abc.tweeter.com",
        instagram="abc.instagram.com",
    )
    assert social_links.user == portfolio_user
    assert social_links.github == "abc@github.com"
    assert social_links.linkedin == "abc.linkedin.com"
    assert social_links.tweeter == "abc.tweeter.com"


@pytest.mark.django_db
def test_portfolio_user_skill_category():
    skill_category = SkillCategory.objects.create(
        category_name="Programming Languages",
    )
    assert skill_category.category_name == "Programming Languages"


@pytest.mark.django_db
def test_portfolio_skill():
    skill_category = SkillCategory.objects.create(
        category_name="Programming Languages",
    )
    skill = Skill.objects.create(
        skill_category=skill_category,
        category_item_name="Python",
    )
    assert skill.category_item_name == "Python"
    assert skill.skill_category == skill_category


@pytest.mark.django_db
def test_portfolio_user_skill():
    user = User.objects.create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email="someone@example.com",
    )
    portfolio_user_skill = UserSkill.objects.create(
        user=user,
        skill_category=SkillCategory.objects.create(
            category_name="Programming Languages"
        ),
        skill=Skill.objects.create(
            skill_category=SkillCategory.objects.create(
                category_name="Programming Languages"
            ),
            category_item_name="Python",
        ),
        summary="Experienced in Python programming",
        rating_out_of_five=4.5,
        total_experience_in_year=5,
        last_used="2023-10-01",
    )
    assert portfolio_user_skill.user == user
    assert portfolio_user_skill.skill.category_item_name == "Python"


@pytest.mark.django_db
def test_review():
    review = Review.objects.create(
        reviewer_name="John Doe",
        reviewer_rating="5",
        review_description="Excellent service and support!",
    )
    assert review.reviewer_name == "John Doe"
    assert review.reviewer_rating == "5"


@pytest.mark.django_db
def test_review_campaign_and_invitation():
    user = User.objects.create(
        username="campaignuser",
        first_name="Campaign",
        last_name="User",
        email="campaign@example.com",
    )
    review = Review.objects.create(
        reviewer_name="John Doe",
        reviewer_rating="5",
        review_description="Excellent service and support!",
    )
    campaign = ReviewCampaign.objects.create(
        name="Launch Campaign",
        message_template="Hi {name}, please review: {link}",
        sender_id="ACME",
        created_by=user,
    )
    invitation = ReviewInvitation.objects.create(
        campaign=campaign,
        recipient_name="John",
        recipient_phone="+15555550100",
        review=review,
        review_url="https://example.com/write-review/?token=abc",
        sms_status="sent",
    )

    assert invitation.campaign == campaign
    assert invitation.review == review
    assert invitation.sms_status == "sent"


@pytest.mark.django_db
def test_new_client():
    new_client = NewClient.objects.create(
        client_email="someone@abc.com",
        created_at="2023-10-01",
    )
    assert new_client.client_email == "someone@abc.com"


@pytest.mark.django_db
def test_client_lead():
    client_lead = ClientLead.objects.create(
        client_name="Jane Doe",
        client_email="someone@abc.com",
        subject="Inquiry about services",
        message="I would like to know more about your services.",
        file_supporting_the_message=None,  # Assuming no file is uploaded
    )
    assert client_lead.client_name == "Jane Doe"
    assert client_lead.client_email == "someone@abc.com"
    assert client_lead.subject == "Inquiry about services"


@pytest.mark.django_db
def test_client_project():
    user = User.objects.create(
        username="testuser",
        first_name="Test",
        last_name="User",
        email="someone@example.com",
    )
    portfolio_user = PortfolioUser.objects.create(
        user=user,
        role="Developer",
        profile_short_description="Short description",
        mobile="1234567890",
        heading="Test Heading",
        headline="Test Headline",
        about="This is a test about section.",
        profile_photo="path/to/photo.jpg",
        work_days="1",
        work_shift="1",
    )
    portfolio_user_skill = UserSkill.objects.create(
        user=user,
        skill_category=SkillCategory.objects.create(
            category_name="Programming Languages"
        ),
        skill=Skill.objects.create(
            skill_category=SkillCategory.objects.create(
                category_name="Programming Languages"
            ),
            category_item_name="Python",
        ),
        summary="Experienced in Python programming",
        rating_out_of_five=4.5,
        total_experience_in_year=5,
        last_used="2023-10-01",
    )
    client_project = ClientProject.objects.create(
        user=portfolio_user,
        project_title="Test Project",
        client_name="Test Client",
        project_url="http://example.com/project",
        project_description="This is a test project description.",
    )
    client_project.tools_and_technologies_used.set([portfolio_user_skill])

    assert client_project.user == portfolio_user
    assert client_project.project_title == "Test Project"
    assert client_project.client_name == "Test Client"
