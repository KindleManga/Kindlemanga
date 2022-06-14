"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView
from django_contact_form.views import ContactFormView
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from manga.forms import CustomContactForm
from manga.models import Manga

info_dict = {
    'queryset': Manga.objects.all(),
    'date_field': 'created',
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("manga.urls", namespace="manga")),
    path('contact/',
         ContactFormView.as_view(
             form_class=CustomContactForm
         ),
         name='django_contact_form'),
    path(
        "sent/",
        TemplateView.as_view(
            template_name="django_contact_form/contact_form_sent.html"
        ),
        name="django_contact_form_sent",
    ),
    path(
        "robots.txt",
        lambda x: HttpResponse(
            """User-agent: GoogleBot
Disallow: /volume/*

User-agent: *
Allow: /
""",
            content_type="text/plain",
        ),
        name="robots_file",
    ),
    path(
        'sitemap.xml', sitemap,
        {'sitemaps': {'manga': GenericSitemap(info_dict, priority=0.6)}},
        name='django.contrib.sitemaps.views.sitemap'
    ),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
