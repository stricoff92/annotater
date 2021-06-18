
from django import forms


class NewTestAnnotation(forms.Form):
    text = forms.CharField(required=False, max_length=1500)
    image_slug = forms.CharField(max_length=50)
    annotate_image_token = forms.CharField(max_length=500)
    load_image_token = forms.CharField(max_length=500)
