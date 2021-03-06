
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count, Sum
from tabulate import tabulate

from memetext.models import AnnotationBatch, AssignedAnnotation, S3Image, TestAnnotation, ControlAnnotation


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        tablefmt = "fancy_grid"

        if not AnnotationBatch.objects.exists():
            print("\n\n  No Annotation Batches  \n\n  🐶  such empty  🐶\n\n")
            return

        batch_count = AnnotationBatch.objects.count()
        batches = AnnotationBatch.objects.values('slug', 'name', 'created_at').order_by("-created_at")
        image_ct_map = {v['batch__slug']: v['ct'] for v in S3Image.objects.values("batch__slug").annotate(ct=Count("batch__slug"))}
        image_flagged_ct_map = {v['batch__slug']: v['ct'] for v in S3Image.objects.filter(is_flagged=True).values("batch__slug").annotate(ct=Count("batch__slug"))}
        test_annotation_ct_map = {v['s3_image__batch__slug']: v['ct'] for v in TestAnnotation.objects.values("s3_image__batch__slug").annotate(ct=Count("s3_image__batch__slug"))}
        ctrl_annotation_ct_map = {v['s3_image__batch__slug']: v['ct'] for v in ControlAnnotation.objects.values("s3_image__batch__slug").annotate(ct=Count("s3_image__batch__slug"))}
        assignment_ct_map = {v['batch__slug']: v['ct'] for v in AssignedAnnotation.objects.values("batch__slug").annotate(ct=Count("batch__slug"))}
        assigned_ct_map = {v['batch__slug']: v['s'] for v in AssignedAnnotation.objects.values("batch__slug").annotate(s=Sum("assigned_count"))}


        rows_to_print = []
        for row in batches:
            rows_to_print.append([
                row['created_at'].strftime("%m/%d/%Y %H:%M"),
                row['slug'],
                row['name'],
                f"{image_ct_map.get(row['slug'], '-')} |{image_flagged_ct_map.get(row['slug'], 0)}⚠️",
                test_annotation_ct_map.get(row['slug'], "-"),
                ctrl_annotation_ct_map.get(row['slug'], "-"),
                assignment_ct_map.get(row['slug'], "-"),
                assigned_ct_map.get(row['slug'], '-'),
            ])

        cols_to_print = ['Created At', 'Slug', 'Name', 'Image Ct', "Test Count", "CTRL Ct", "Assignment Ct", "Max Assigned"]

        print(f"\n ANNOTATION BATCHES ({batch_count})\n")
        print(tabulate(rows_to_print, cols_to_print, tablefmt=tablefmt))
        print("\n")

        print(" Assigned Users")
        assigned_users = list(AssignedAnnotation.objects.values_list("user__username", "user_id", "batch__name", "assigned_count"))
        print(tabulate(assigned_users, ['Username', "User ID", 'Batch', 'Assigned Count'], tablefmt=tablefmt))
        print("\n")
