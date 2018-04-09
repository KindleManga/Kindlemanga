from django.urls import path
from .views import MangaListView, MangaDetailView, VolumeView

urlpatterns = [
    path('', MangaListView.as_view(), name="manga_list"),
    path('<slug:slug>/', MangaDetailView.as_view(), name='manga_detail'),
    path('volume/<int:pk>/', VolumeView.as_view(), name='volume'),
]
