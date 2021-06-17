from django.contrib import admin

from memetext.models import (
    AnnotationBatch,
    S3Image,
    TestAnnotation,
    ControlAnnotation,
    AssignedAnnotation,
    Payment,
    PayoutRate,
)

# Register your models here.

admin.site.register(AnnotationBatch)
admin.site.register(S3Image)
admin.site.register(TestAnnotation)
admin.site.register(ControlAnnotation)
admin.site.register(AssignedAnnotation)
admin.site.register(Payment)
admin.site.register(PayoutRate)
