

from django.urls import path

from memetext import web_views, api_views

api_view_prefix = "api/"

urlpatterns = [
    # webviews
    path("", web_views.landing, name="memetext-web-landing"),
    path("add-annotation", web_views.add_annotation, name="memetext-web-add-annotation"),

    # api views
    path(
        "api/get-image/<slug:assignment_slug>",
        api_views.get_image_to_annotate,
        name="memetext-api-get-image",
    ),
    path(
        "api/download-image/<slug:assignment_slug>/<slug:image_slug>",
        api_views.download_image,
        name="memetext-api-download-image",
    ),
    path(
        "api/new-test-annotation",
        api_views.add_test_annotation,
        name="memetext-api-new-test-annotation",
    ),
    path(
        "api/admin/new-control-annotation",
        api_views.add_control_annotation,
        name="memetext-api-new-control-annotation",
    ),
    path(
        "api/admin/download-image/<slug:image_slug>",
        api_views.admin_download_image,
        name="memetext-api-new-control-annotation",
    ),
]

