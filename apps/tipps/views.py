import datetime
from urllib.parse import urlsplit, urlunsplit

import vobject
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.front.mixins import LoginRequiredMixin
from apps.tipps import forms, models


class TippList(ListView):
    paginate_by = 50
    model = models.Tipp

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
