

from django.urls import path
from two_factor.views import  QRGeneratorView

from website import views

urlpatterns = [
    path("", views.landing, name="anon-landing"),
    path("login-with-link", views.login_with_magic_link, name="anon-login-with-link"),
    path("logout", views.logout_page, name="user-logout")
]
