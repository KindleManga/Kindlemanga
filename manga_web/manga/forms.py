from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
from django import forms
from django_contact_form.forms import ContactForm

from .models import Manga, Volume
from .tasks import make_volume


class CreateVolumeForm(forms.Form):
    # captcha = ReCaptchaField(widget=ReCaptchaV3)

    def create_volume(self, volume_id):
        r = make_volume.delay(volume_id)
        return r


class SearchForm(forms.Form):
    name = forms.CharField()


class CustomContactForm(ContactForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3)
