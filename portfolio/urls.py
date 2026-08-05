from django.urls import include, path

from . import views as portfolio_view

urlpatterns = [
    path("", portfolio_view.index, name="index"),
    # path(
    #     "check_input_existence/",
    #     portfolio_view.check_input_existence,
    #     name="check_input_existence",
    # ),
    # path("user_signup/", portfolio_view.user_signup, name="user_signup"),
    # path("user_login/", portfolio_view.user_login, name="user_login"),
    # path("user_logout/", portfolio_view.user_logout, name="user_logout"),
    path(
        "tech_details/<int:tech_id>", portfolio_view.tech_details, name="tech_details"
    ),
    path("new_client_feed/", portfolio_view.new_client_feed, name="new_client_feed"),
    path("contact_us/", portfolio_view.contact_us, name="contact_us"),
    path("about_me/", portfolio_view.about_me, name="about_me"),
    path("write-review/", portfolio_view.write_review, name="write_review"),
    path("user_portfolio/", portfolio_view.user_portfolio, name="user_portfolio"),
    path(
        "user_profile_details/",
        portfolio_view.user_profile_details,
        name="user_profile_details",
    ),
    path("froala_editor/", include("froala_editor.urls")),
]
