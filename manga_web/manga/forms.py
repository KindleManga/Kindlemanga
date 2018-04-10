from django import forms
from .tasks import make_volume


class CreateVolumeForm(forms.Form):
    email = forms.EmailField()

    def create_volume(self, volume_id):
        r = make_volume(volume_id)
        return r
