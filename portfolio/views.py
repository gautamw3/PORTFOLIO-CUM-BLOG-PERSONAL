import logging
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import EmailMessage
from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from portfolio_cum_blog import settings

from .constants import SUB_CLIENT_LEAD_EMAIL
from .forms import ContactUs, ReviewSubmissionForm
from .models import (
    ClientProject,
    NewClient,
    PortfolioUser,
    PortfolioUserAddress,
    PortfolioUserSocialMediaLink,
    Resume,
    Review,
    ReviewInvitation,
    UserSkill,
)

logger = logging.getLogger(__name__)


class GlobalResponse:
    """
    Builds a consistent AJAX response payload for view handlers.
    """

    def __init__(self):
        self.response_data = {
            "response": "",
            "responseMessage": "",
            "responseMessageInfo": "",
        }

    def get_response_obj(self):
        return self.response_data


class GlobalUser:
    """
    Resolves the configured default portfolio user.
    """

    def __init__(self, user_model):
        self.pk = settings.DEFAULT_USER
        self.user_model = user_model
        self.user_obj = None

    def get_user_obj(self):
        self.user_obj = self.user_model.objects.get(pk=self.pk)
        return self.user_obj


def get_global_response(request):
    """
    Return the standard response dictionary used in JSON endpoints.
    """
    global_response_obj = GlobalResponse()
    response_data = global_response_obj.get_response_obj()
    return response_data


def get_global_user(request=None):
    """
    Return the fallback user object configured by DEFAULT_USER.
    """
    global_user_obj = GlobalUser(User)
    obj_user = global_user_obj.get_user_obj()
    return obj_user


def get_user_skills(user_id):
    """
    Build the categorized skill payload for a given user.
    """
    test_flag = False
    obj_user_skills = UserSkill.objects.filter(user__id=user_id)
    skills = {}
    for each_item in obj_user_skills:
        rating = int(each_item.get_rating_out_of_five_display())
        if rating == 5:
            progress_bar_color = 1
        elif rating == 4:
            progress_bar_color = 7
        elif rating == 3:
            progress_bar_color = 4
        elif rating == 2:
            progress_bar_color = 3
        else:
            progress_bar_color = 2
        if each_item.skill_category.get_category_name_display() in skills:
            skills[each_item.skill_category.get_category_name_display()].append(
                {
                    each_item.skill.category_item_name: {
                        "id": each_item.skill.id,
                        "summary": each_item.summary,
                        "description": each_item.description,
                        "logo": each_item.skill.category_item_image.url,
                        "total_experience_in_year": (
                            each_item.get_total_experience_in_year_display()
                        ),
                        "rating_out_of_five": rating * 20,
                        "progress_bar_color": progress_bar_color,
                    }
                }
            )
        else:
            skills[each_item.skill_category.get_category_name_display()] = [
                {
                    each_item.skill.category_item_name: {
                        "id": each_item.skill.id,
                        "summary": each_item.summary,
                        "description": each_item.description,
                        "logo": each_item.skill.category_item_image.url,
                        "total_experience_in_year": (
                            each_item.get_total_experience_in_year_display()
                        ),
                        "rating_out_of_five": rating * 20,
                        "progress_bar_color": progress_bar_color,
                        "test_flag": test_flag,
                    }
                }
            ]
    return skills


def get_customer_reviews():
    """Fetch five random customer reviews for homepage/testimonial sections."""
    obj_customer_reviews = Review.objects.filter(is_approved=True).order_by("?")[:5]
    customer_reviews = []
    for each_review in obj_customer_reviews:
        customer_review = {
            "reviewer": each_review.reviewer_name,
            "rating": [
                i for i in range(int(each_review.get_reviewer_rating_display()))
            ],
            "description": each_review.review_description,
        }
        customer_reviews.append(customer_review)
    return customer_reviews


def get_review_invitation_by_token(token_value):
    """Resolve an invitation record from the token query string."""
    if not token_value:
        return None
    try:
        return ReviewInvitation.objects.select_related("campaign").get(
            token=token_value
        )
    except ReviewInvitation.DoesNotExist:
        logger.info("No review invitation found for token=%s", token_value)
        return None


def build_public_review_link(request, token_value=None):
    """Create the public review URL, with an optional token query string."""
    review_link = request.build_absolute_uri(reverse("write_review"))
    if token_value:
        review_link = f"{review_link}?{urlencode({'token': token_value})}"
    return review_link


def get_social_media_links(portfolio_user_id):
    """Return social links for a portfolio user, if available."""
    try:
        obj_social_media_links = PortfolioUserSocialMediaLink.objects.get(
            user_id=portfolio_user_id
        )
    except PortfolioUserSocialMediaLink.DoesNotExist:
        logger.info(
            "No social media links found for portfolio user id=%s",
            portfolio_user_id,
        )
        obj_social_media_links = None
    except PortfolioUserSocialMediaLink.MultipleObjectsReturned:
        logger.warning(
            "Multiple social link records found for portfolio user id=%s; using first",
            portfolio_user_id,
        )
        obj_social_media_links = PortfolioUserSocialMediaLink.objects.filter(
            user_id=portfolio_user_id
        ).first()
    return obj_social_media_links


def embed_social_media_links_to_context(context, obj_social_media_links):
    """Attach social links to a template context dictionary."""
    if obj_social_media_links is not None:
        context["github"] = obj_social_media_links.github
        context["linkedin"] = obj_social_media_links.linkedin
        context["tweeter"] = obj_social_media_links.tweeter
        context["instagram"] = obj_social_media_links.instagram
    return context


def index(request):
    """Render the landing page with user profile, skills, and reviews."""
    template = "portfolio/index.html"
    try:
        obj_user = get_global_user()
        obj_portfolio_user = PortfolioUser.objects.get(pk=obj_user.user_portfolio.id)
        email = obj_user.email
        mobile = obj_portfolio_user.mobile
        customer_reviews = get_customer_reviews()
        skills = get_user_skills(obj_user.id)
        heading = obj_portfolio_user.heading
        headline = obj_portfolio_user.headline
        profile_short_description = obj_portfolio_user.profile_short_description
        role = obj_portfolio_user.role
        about = obj_portfolio_user.about
        profile_photo = (
            obj_portfolio_user.profile_photo.url
            if obj_portfolio_user.profile_photo
            else "#"
        )
        obj_social_media_links = get_social_media_links(obj_portfolio_user.id)
        obj_resume = Resume.objects.filter(user_id=obj_portfolio_user.id).first()
        resume_url = "#"
        if obj_resume:
            resume_url = obj_resume.resume_file.url
        context = {
            "page_title": "Home",
            "heading": heading,
            "headline": headline,
            "profile_short_description": profile_short_description,
            "role": role,
            "email": email,
            "mobile": mobile,
            "profile_photo": profile_photo,
            "resume_url": resume_url,
            "about": about,
            "skills": skills,
            "customer_reviews": customer_reviews,
        }
        context = embed_social_media_links_to_context(context, obj_social_media_links)
        logger.info("Rendered index page for user id=%s", obj_user.id)
    except (ObjectDoesNotExist, AttributeError, TypeError, ValueError) as err:
        logger.exception("Failed to render index page")
        context = {"page_title": "Home", "exception": err.__str__()}
    return render(request, template, context)


def write_review(request):
    """Render the public review form and store a customer review submission."""
    template = "portfolio/write_review.html"
    token_value = request.GET.get("token") or request.POST.get("token")
    invitation = get_review_invitation_by_token(token_value)
    review_form = ReviewSubmissionForm(
        initial={
            "token": token_value or "",
            "reviewer_name": invitation.recipient_name if invitation else "",
        }
    )
    context = {
        "page_title": "Write a Review",
        "review_form": review_form,
        "review_invitation": invitation,
        "customer_reviews": get_customer_reviews(),
    }
    try:
        if request.method == "POST":
            review_form = ReviewSubmissionForm(request.POST)
            context["review_form"] = review_form
            if review_form.is_valid():
                review = Review.objects.create(
                    reviewer_name=review_form.cleaned_data["reviewer_name"].strip(),
                    reviewer_rating=review_form.cleaned_data["reviewer_rating"],
                    review_description=review_form.cleaned_data["review_description"],
                )
                if invitation is not None:
                    invitation.review = review
                    invitation.sms_status = "reviewed"
                    invitation.reviewed_at = timezone.now()
                    invitation.save(
                        update_fields=[
                            "review",
                            "sms_status",
                            "reviewed_at",
                            "updated_at",
                        ]
                    )
                context["response"] = "success"
                context["responseMessage"] = "Thank you for sharing your review."
                context["responseMessageInfo"] = (
                    "Your feedback was received and will be published after admin approval."
                )
                logger.info(
                    "Customer review submitted for reviewer=%s",
                    review.reviewer_name,
                )
            else:
                context["response"] = "error"
                context["responseMessage"] = "Review submission failed"
                context["responseMessageInfo"] = "Please correct the highlighted fields."
        elif request.method != "GET":
            logger.warning(
                "Write review endpoint called with invalid HTTP method=%s",
                request.method,
            )
            context["response"] = "error"
            context["responseMessage"] = "Review submission failed"
            context["responseMessageInfo"] = f"Invalid HTTP method {request.method}"
    except (ValidationError, DatabaseError, TypeError, ValueError) as err:
        logger.exception("Failed to process review submission")
        context["response"] = "error"
        context["responseMessage"] = "Review submission failed"
        context["responseMessageInfo"] = err.__str__()
    return render(request, template, context)


# def user_signup(request):
#     """
#     Register a new user and associated portfolio profile.
#     """
#     response_data = get_global_response(request)
#     user_email = None
#     try:
#         if request.method == "POST":
#             first_name = request.POST.get("firstName")
#             last_name = request.POST.get("lastName")
#             user_email = request.POST.get("userMail")
#             user_mobile = request.POST.get("userMobile")
#             user_password = request.POST.get("password")
#             if (
#                 first_name
#                 and last_name
#                 and user_email
#                 and user_mobile
#                 and user_password
#             ):
#                 user = User.objects.create_user(
#                     username=user_email, email=user_email, password=user_password
#                 )
#                 user.first_name = first_name
#                 user.last_name = last_name
#                 user.save()
#                 obj_portfolio_user = PortfolioUser(
#                     user=user,
#                     mobile=user_mobile,
#                 )
#                 obj_portfolio_user.save()
#                 user = authenticate(username=user_email, password=user_password)
#                 if user is not None:
#                     login(request, user)
#                 logger.info("User registration successful for email=%s", user_email)
#                 response_data["response"] = "success"
#                 response_data["responseMessage"] = (
#                     "You have been registered successfully"
#                 )
#                 response_data["responseMessageInfo"] = "Redirecting to the dashboard"
#             else:
#                 logger.warning("Registration rejected due to missing required fields")
#                 response_data["response"] = "warning"
#                 response_data["responseMessage"] = "Registration Failed"
#                 response_data["responseMessageInfo"] = (
#                     "Invalid input/please check if each and every mandatory details"
#                     " were provided or not!"
#                 )
#         else:
#             logger.warning(
#                 "Registration endpoint called with invalid HTTP method=%s",
#                 request.method,
#             )
#             response_data["response"] = "error"
#             response_data["responseMessage"] = "Registration Failed"
#             response_data["responseMessageInfo"] = (
#                 f"Invalid HTTP method {request.method}"
#             )
#     except (IntegrityError, ValidationError, TypeError, ValueError) as err:
#         logger.exception("Registration failed for email=%s", user_email)
#         response_data["response"] = "error"
#         response_data["responseMessage"] = "Registration Failed"
#         response_data["responseMessageInfo"] = str(err)
#     return JsonResponse(response_data)


# def user_login(request):
#     """
#     Authenticate and sign in a user.
#     """
#     response_data = get_global_response(request)
#     user_email = None
#     try:
#         if request.method == "POST":
#             user_email = request.POST.get("userMailSignIn")
#             user_password = request.POST.get("passwordSignIn")
#             if user_email and user_password:
#                 user = authenticate(username=user_email, password=user_password)
#                 if user is not None:
#                     login(request, user)
#                     logger.info("User login successful for email=%s", user_email)
#                     response_data["response"] = "success"
#                     response_data["responseMessage"] = "Login successful"
#                     response_data["responseMessageInfo"] = (
#                         "Redirecting to the dashboard"
#                     )
#                 else:
#                     logger.warning("User login failed due to invalid credentials")
#                     response_data["response"] = "error"
#                     response_data["responseMessage"] = "Login failed"
#                     response_data["responseMessageInfo"] = "Invalid user"
#         else:
#             logger.warning(
#                 "Login endpoint called with invalid HTTP method=%s",
#                 request.method,
#             )
#             response_data["response"] = "error"
#             response_data["responseMessage"] = "Login failed"
#             response_data["responseMessageInfo"] = (
#                 f"Invalid HTTP method {request.method}"
#             )
#     except (ValidationError, TypeError, ValueError) as err:
#         logger.exception("Login failed for email=%s", user_email)
#         response_data["response"] = "error"
#         response_data["responseMessage"] = "Login failed"
#         response_data["responseMessageInfo"] = str(err)
#     return JsonResponse(response_data)


# def user_logout(request):
#     """
#     Sign out the current user.
#     """
#     user_id = request.user.id if request.user.is_authenticated else None
#     logger.info("User logout requested for user id=%s", user_id)
#     logout(request)
#     return redirect(reverse("index"))


def tech_details(request, tech_id):
    """
    Render details for one technology entry for the active/default user.
    """
    template = "portfolio/tech_details.html"
    context = {
        "page_title": "Technology details",
        "banner_heading_pref": "Technology",
        "page_details": {},
    }
    try:
        obj_user = get_global_user()
        if request.method == "GET":
            obj_tech_details = UserSkill.objects.get(
                user__id=obj_user.id, skill__id=tech_id
            )
            obj_social_media_links = get_social_media_links(
                obj_tech_details.user.user_portfolio.id
            )
            context = embed_social_media_links_to_context(
                context, obj_social_media_links
            )
            breadcrumb_mid_item_cat_list = (
                obj_tech_details.skill_category.get_category_name_display().split()
            )
            if len(breadcrumb_mid_item_cat_list) > 1:
                context["page_details"]["heading"] = (
                    f"{obj_tech_details.skill.category_item_name} "
                    f"{breadcrumb_mid_item_cat_list[0]} "
                    f"{breadcrumb_mid_item_cat_list[1]}"
                )
            else:
                context["page_details"]["heading"] = (
                    f"{obj_tech_details.skill.category_item_name} "
                    f"{obj_tech_details.skill_category.get_category_name_display()}"
                )
            context["page_details"][
                "breadcrumb_mid_item"
            ] = obj_tech_details.skill.category_item_name
            context["page_details"]["summary"] = obj_tech_details.summary
            context["page_details"]["description"] = obj_tech_details.description
            context["page_details"]["rating"] = [
                i for i in range(int(obj_tech_details.rating_out_of_five))
            ]
            context["page_details"][
                "total_experience"
            ] = obj_tech_details.get_total_experience_in_year_display()
            context["page_details"]["last_used"] = obj_tech_details.last_used
            context["page_details"][
                "image"
            ] = obj_tech_details.skill.category_item_image.url
        else:
            logger.warning(
                "Tech details endpoint called with invalid HTTP method=%s",
                request.method,
            )
            context["error"] = f"Invalid request method: {request.method}!"
    except UserSkill.DoesNotExist as err:
        logger.exception("Tech details not found for tech_id=%s", tech_id)
        context["page_details"] = None
        context["exception"] = err.__str__()
    except (
        ObjectDoesNotExist,
        ValidationError,
        DatabaseError,
        AttributeError,
        TypeError,
        ValueError,
    ) as err:
        logger.exception("Failed to render tech details for tech_id=%s", tech_id)
        context["page_details"] = None
        context["exception"] = err.__str__()
    return render(request, template, context)


def new_client_feed(request):
    """
    Stores the email address of the client who shown interest in
    submitting their email address
    """
    response_data = get_global_response(request)
    try:
        if request.method == "POST":
            client_email = request.POST.get("new_client_email")
            if client_email:
                obj_new_client_email = NewClient(client_email=client_email)
                obj_new_client_email.save()
                logger.info("New client lead captured for email=%s", client_email)
                response_data["response"] = "success"
                response_data["responseMessage"] = "We got that"
                response_data["responseMessageInfo"] = (
                    "Thanks for showing interest in availing our services"
                )
            else:
                logger.warning("New client feed submitted without email")
                response_data["response"] = "error"
                response_data["responseMessage"] = "Something went wrong"
                response_data["responseMessageInfo"] = "Email is required"
        else:
            logger.warning(
                "New client feed endpoint called with invalid HTTP method=%s",
                request.method,
            )
            response_data["response"] = "error"
            response_data["responseMessage"] = "Something went wrong"
            response_data["responseMessageInfo"] = "Invalid HTTP request"
    except (ValidationError, DatabaseError, TypeError, ValueError) as err:
        logger.exception("Failed to save new client lead")
        response_data["response"] = "error"
        response_data["responseMessage"] = err.__str__()
        response_data["responseMessageInfo"] = "Please try after sometime"
    return JsonResponse(response_data)


def send_new_client_lead_mail(email_data):
    """Send acknowledgement email for a submitted client lead."""
    template = "portfolio/email_templates/new_client_lead.html"
    message_to_attach = get_template(template).render(email_data)
    email_message = EmailMessage(
        SUB_CLIENT_LEAD_EMAIL,
        message_to_attach,
        settings.APPLICATION_EMAIL,
        [email_data["client_email"]],
        reply_to=[settings.APPLICATION_EMAIL],
    )
    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)
    logger.info("Acknowledgement email sent to %s", email_data["client_email"])


def contact_us(request):
    """
    Render and process the contact-us form.
    """
    template = "portfolio/contact_us.html"
    context = {"page_title": "Contact us"}
    try:
        obj_user = get_global_user()
        if request.method == "POST":
            form = ContactUs(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                email_data = {
                    "client_name": request.POST["client_name"],
                    "client_email": request.POST["client_email"],
                    "subject": request.POST["subject"],
                    "message": request.POST["message"],
                }
                send_new_client_lead_mail(email_data)
                logger.info(
                    "Contact form submitted successfully for email=%s",
                    email_data["client_email"],
                )
                context["response"] = "success"
                form = ContactUs()
            else:
                logger.warning("Contact form validation failed")
                context["response"] = "error"
        else:
            form = ContactUs()
        try:
            obj_user_address = PortfolioUserAddress.objects.get(
                user_id=obj_user.user_portfolio.id
            )
        except PortfolioUserAddress.DoesNotExist:
            obj_user_address = None
        obj_social_media_links = get_social_media_links(obj_user.user_portfolio.id)
        context = embed_social_media_links_to_context(context, obj_social_media_links)
        if obj_user_address is not None:
            context["country"] = obj_user_address.country
            context["state"] = obj_user_address.state
            context["city"] = obj_user_address.city
            context["mobile"] = obj_user.user_portfolio.mobile
            context["email"] = obj_user.email
            context["work_days"] = obj_user.user_portfolio.get_work_days_display()
            context["work_shift"] = obj_user.user_portfolio.get_work_shift_display()
        context["form"] = form
    except (
        ObjectDoesNotExist,
        ValidationError,
        DatabaseError,
        AttributeError,
        TypeError,
        ValueError,
    ) as err:
        logger.exception("Failed to process contact-us request")
        context["exception"] = err.__str__()
    return render(request, template, context)


def about_me(request):
    """
    Renders the about page
    """
    template = "portfolio/about-me.html"
    context = {
        "page_title": "About me",
    }
    try:
        obj_user = get_global_user()
        if request.method == "GET":
            context["about"] = obj_user.user_portfolio.about
            context["role"] = obj_user.user_portfolio.role
            context["profile_photo"] = (
                obj_user.user_portfolio.profile_photo.url
                if obj_user.user_portfolio.profile_photo
                else "#"
            )
            obj_resume = Resume.objects.filter(
                user_id=obj_user.user_portfolio.id
            ).first()
            context["resume_url"] = obj_resume.resume_file.url if obj_resume else "#"
            customer_reviews = get_customer_reviews()
            obj_social_media_links = get_social_media_links(obj_user.user_portfolio.id)
            context = embed_social_media_links_to_context(
                context, obj_social_media_links
            )
            context["customer_reviews"] = customer_reviews
        else:
            logger.warning(
                "About page called with invalid HTTP method=%s",
                request.method,
            )
            context["error"] = "Invalid HTTP method detected"
    except (ObjectDoesNotExist, AttributeError, TypeError, ValueError) as err:
        logger.exception("Failed to render about page")
        context["exception"] = err.__str__()
    return render(request, template, context)


def user_portfolio(request):
    """
    Loads the portfolio page
    """
    template = "portfolio/portfolio.html"
    context = {"page_title": "User Portfolio"}
    try:
        obj_user = get_global_user()
        if request.method == "GET":
            obj_social_media_links = get_social_media_links(obj_user.user_portfolio.id)
            skills = get_user_skills(obj_user.id)
            context["heading"] = obj_user.user_portfolio.heading
            context["headline"] = obj_user.user_portfolio.headline
            context["skills"] = skills
            context = embed_social_media_links_to_context(
                context, obj_social_media_links
            )
        else:
            logger.warning(
                "Portfolio page called with invalid HTTP method=%s",
                request.method,
            )
            context["error"] = "Invalid HTTP method detected"
    except (ObjectDoesNotExist, AttributeError, TypeError, ValueError) as err:
        logger.exception("Failed to render user portfolio page")
        context["exception"] = err.__str__()
    return render(request, template, context)


def user_profile_details(request, user_id=None):
    """
    Loads user profile details page
    """
    template = "portfolio/profile_details.html"
    context = {"page_title": "Profile details"}
    obj_portfolio_user = None
    try:
        obj_user = get_global_user()
        if request.method == "GET":
            profile_user_id = user_id if user_id is not None else obj_user.id
            obj_portfolio_user = PortfolioUser.objects.get(user_id=profile_user_id)
            obj_resume = Resume.objects.filter(user_id=obj_portfolio_user.id).first()
            obj_social_media_links = get_social_media_links(obj_portfolio_user.id)
            skills = get_user_skills(obj_portfolio_user.id)
            obj_client_projects = ClientProject.objects.filter(
                user_id=obj_portfolio_user.id
            )
            client_project_list = []
            for each_client_project in obj_client_projects:
                obj_tools_and_tech = (
                    each_client_project.tools_and_technologies_used.all()
                )
                tools_and_tech_list = [
                    each_tool_and_tech.skill.category_item_name
                    for each_tool_and_tech in obj_tools_and_tech
                ]
                client_project_list.append(
                    {
                        "project_title": each_client_project.project_title,
                        "client_name": each_client_project.client_name,
                        "project_url": each_client_project.project_url,
                        "tools_and_technologies_used": tools_and_tech_list,
                        "project_description": each_client_project.project_description,
                    }
                )
            context["client_project_list"] = client_project_list
            context["role"] = obj_portfolio_user.role
            context["profile_short_description"] = obj_portfolio_user.about
            context["mobile"] = obj_portfolio_user.mobile
            context["email"] = obj_portfolio_user.user.email
            context["about"] = obj_portfolio_user.about
            context["profile_photo"] = obj_portfolio_user.profile_photo.url
            context["user_first_name"] = obj_portfolio_user.user.first_name
            context["resume_url"] = obj_resume.resume_file.url if obj_resume else "#"
            context["skills"] = skills
            context = embed_social_media_links_to_context(
                context, obj_social_media_links
            )
        else:
            logger.warning(
                "User profile details called with invalid HTTP method=%s",
                request.method,
            )
            context["error"] = "Invalid HTTP method detected"
    except PortfolioUser.DoesNotExist as err:
        logger.exception("Profile details not found for user_id=%s", request.user.id)
        context["exception"] = err.__str__()
    except (
        ObjectDoesNotExist,
        ValidationError,
        DatabaseError,
        AttributeError,
        TypeError,
        ValueError,
    ) as err:
        logger.exception(
            "Failed to render profile details for user_id=%s",
            getattr(obj_portfolio_user, "id", None),
        )
        context["exception"] = err.__str__()
    return render(request, template, context)


# def check_input_existence(request):
#     """Validate whether an email or mobile value is already present."""
#     if request.method != "GET":
#         logger.warning(
#             "Input existence endpoint called with invalid HTTP method=%s",
#             request.method,
#         )
#         return JsonResponse(
#             {
#                 "response": False,
#                 "responseMessage": "Invalid HTTP method",
#                 "responseMessageInfo": "Only GET requests are allowed",
#             }
#         )
#     try:
#         input_value = request.GET.get("inputValue")
#         input_type = request.GET.get("inputField")
#         if not input_value or not input_type:
#             logger.warning("Input existence check failed: missing parameters")
#             return JsonResponse(
#                 {
#                     "response": False,
#                     "responseMessage": "Missing parameters",
#                     "responseMessageInfo": "inputValue and inputField are required",
#                 }
#             )
#         if input_type == "email":
#             exists = User.objects.filter(email=input_value).exists()
#         elif input_type == "mobile":
#             exists = PortfolioUser.objects.filter(mobile=input_value).exists()
#         else:
#             logger.warning("Input existence check failed: invalid input type")
#             return JsonResponse(
#                 {
#                     "response": False,
#                     "responseMessage": "Invalid input type",
#                     "responseMessageInfo": "inputField must be email or mobile",
#                 }
#             )
#         return JsonResponse(
#             {
#                 "response": exists,
#                 "responseMessage": "Input existence checked successfully",
#             }
#         )
#     except (DatabaseError, TypeError, ValueError) as err:
#         logger.exception("Input existence check failed unexpectedly")
#         return JsonResponse(
#             {
#                 "response": False,
#                 "responseMessage": str(err),
#                 "responseMessageInfo": (
#                     "An error occurred while checking input existence"
#                 ),
#             }
#         )
