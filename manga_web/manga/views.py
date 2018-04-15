from functools import reduce

from django.views.generic import ListView, DetailView
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.db.models import Q
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import Manga, Volume
from .forms import CreateVolumeForm, SearchForm


class HomeView(FormView):
    template_name = 'manga/index.html'
    form_class = SearchForm
    success_url = reverse_lazy()


def search_ajax(request):
    if request.method == 'GET':
        keywords = request.GET.get('q')
        qs = Manga.objects.filter(
            reduce(lambda x, y: x | y, [Q(name__unaccent__icontains=word) for word in keywords.split()])
        )[:10]
        data = {'results': [i.as_dict() for i in qs]}
        return JsonResponse(data)


class MangaSearchView(ListView):
    model = Manga
    paginate_by = 10
    context_object_name = 'mangas'
    template_name = 'manga/search_result.html'

    def get_context_data(self, **kwargs):
        context = super(MangaSearchView, self).get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q')
        return context

    def get_queryset(self):
        keywords = self.request.GET.get('q')
        if keywords:
            qs = Manga.objects.filter(
                reduce(lambda x, y: x | y, [Q(name__unaccent__icontains=word) for word in keywords.split()])
            )
            return qs


class MangaListView(ListView):
    model = Manga
    context_object_name = 'mangas'
    paginate_by = 8
    ordering = 'name'


class MangaDetailView(DetailView):
    model = Manga
    context_object_name = 'manga'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manga = self.get_object()
        context['volume_list'] = manga.volume_set.all().order_by('number')
        return context


class VolumeView(FormView):
    template_name = 'manga/volume.html'
    form_class = CreateVolumeForm
    success_url = '/thanks/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volume_id = self.kwargs['pk']
        volume = Volume.objects.get(pk=volume_id)
        context['volume'] = volume
        return context

    def form_valid(self, form):
        volume_id = self.kwargs['pk']
        form.create_volume(volume_id)
        return super().form_valid(form)


class FAQView(TemplateView):
    template_name = "manga/faq.html"


class ContactView(TemplateView):
    template_name = "manga/contact.html"


class ThanksView(TemplateView):
    template_name = "manga/thanks.html"
