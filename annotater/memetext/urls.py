

from django.urls import path

from memetext import web_views, api_views

api_view_prefix = "api/"

urlpatterns = [
    # webviews
    path("", web_views.landing, name="memetext-web-landing"),

    path("add-annotation", web_views.add_annotation, name="memetext-web-add-annotation"),

    # api views
]

