from django import forms
from captcha.fields import ReCaptchaField

from .tasks import make_volume


class CreateVolumeForm(forms.Form):
    email = forms.EmailField()
    captcha = ReCaptchaField()

    def create_volume(self, volume_id):
        r = make_volume(volume_id)
        return r


class SearchForm(forms.Form):
    name = forms.CharField()