

from django.urls import path
from django.contrib.auth.views import LoginView


from website import views


LOGIN_VIEW_EXTRA_CONTEXT = dict(
    title=' Login',
    site_title='Annotater',
    site_header='Welcome Back 👋',
)
LOGIN_VIEW_KWARGS = dict(
    template_name='admin/login.html',
    extra_context=LOGIN_VIEW_EXTRA_CONTEXT,
)


urlpatterns = [
    path("", views.landing, name="anon-landing"),
    path("login-with-cred", LoginView.as_view(**LOGIN_VIEW_KWARGS)),
    path("login-with-link", views.login_with_magic_link, name="anon-login-with-link"),
    path("logout", views.logout_page, name="user-logout")
]
