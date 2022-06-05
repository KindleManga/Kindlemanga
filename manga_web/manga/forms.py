from captcha.fields import ReCaptchaField
from django import forms

from .models import Manga, Volume
from .tasks import make_volume, send_notification


class CreateVolumeForm(forms.Form):
    email = forms.EmailField()
    captcha = ReCaptchaField()

    def create_volume(self, volume_id, email):
        r = make_volume(volume_id, email)
        return r


class SearchForm(forms.Form):
    name = forms.CharField()
