

from django.urls import path

from memetext import web_views, api_views

api_view_prefix = "api/"

urlpatterns = [
    # webviews
    path("", web_views.landing, name="memetext-web-landing"),
    path("add-annotation", web_views.add_annotation, name="memetext-web-add-annotation"),
    path("add-control-annotation", web_views.add_control_annotation, name="memetext-web-add-control-annotation"),
    path("annotation-audit-report", web_views.view_annotation_audit, name="memetext-annotation-audit"),

    # api views

    # Test annotation
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
        "api/flag-image/<slug:image_slug>",
        api_views.flag_image,
        name="memetext-api-flag-image",
    ),

    # Control Annotations
    path(
        "api/admin/download-image/<slug:image_slug>",
        api_views.admin_download_image,
        name="memetext-api-admin-download-image",
    ),
    path(
        "api/admin/new-control-annotation",
        api_views.add_control_annotation,
        name="memetext-api-new-control-annotation",
    ),

]

