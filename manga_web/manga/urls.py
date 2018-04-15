from django.urls import path
from .views import (
    MangaListView, MangaDetailView, MangaSearchView,
    VolumeView, HomeView, FAQView, ContactView,
    search_ajax
)

app_name = "manga"
urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('faq/', FAQView.as_view(), name="faq"),
    path('contact/', ContactView.as_view(), name="contact"),
    path('ajax/search/', search_ajax, name="search_ajax"),
    path('manga/', MangaListView.as_view(), name="list"),
    path('search/', MangaSearchView.as_view(), name="search"),
    path('manga/<slug:slug>/', MangaDetailView.as_view(), name='detail'),
    path('volume/<int:pk>/', VolumeView.as_view(), name='volume'),
]
