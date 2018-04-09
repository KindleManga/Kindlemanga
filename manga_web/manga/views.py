from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from .models import Manga, Volume
from .forms import CreateVolumeForm


class MangaListView(ListView):
    model = Manga
    context_object_name = 'mangas'
    paginate_by = 6


class MangaDetailView(DetailView):
    model = Manga
    context_object_name = 'manga'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manga = self.get_object()
        context['volume_list'] = manga.volume_set.all()
        return context


class VolumeView(FormView):
    template_name = 'manga/volume.html'
    form_class = CreateVolumeForm
    success_url = '/thanks/'

    def form_valid(self, form):
        volume_id = self.kwargs['pk']
        form.create_volume(volume_id)
        return super().form_valid(form)
