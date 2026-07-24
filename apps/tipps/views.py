import datetime
from urllib.parse import urlsplit, urlunsplit

import vobject
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from rest_framework.views import APIView

from apps.front.message_levels import EVENT
from apps.front.mixins import LoginRequiredMixin
from apps.tipps import forms, models


# FIXME: duplicated
def extend_tipps_with_votes(tipps, user_pk):
    """Extends a tipp queryset with tipp votes (using an extra()-query)."""

    vote_base_query = "SELECT EXISTS (SELECT id \
            FROM tipps_tippvote \
            WHERE tipps_tippvote.tipp_id = tipps_tipp.id \
            AND vote = '%s' \
            AND user_id = %u)"
    count_query = "SELECT COUNT(*) \
            FROM tipps_tippvote \
            WHERE tipps_tippvote.tipp_id = tipps_tipp.id"
    count_base_query = count_query + " AND vote = '%s'"

    return tipps.extra(
        select={
            "voted_up": False if user_pk is None else vote_base_query % ("t", user_pk),
            "voted_down": (
                False if user_pk is None else vote_base_query % ("f", user_pk)
            ),
            "vote_count": count_query,
            "upvote_count": count_base_query % "t",
            "downvote_count": count_base_query % "f",
        },
    )


class TippList(ListView):
    paginate_by = 50

    def get_queryset(self):
        return extend_tipps_with_votes(models.Tipp.objects.all(), self.request.user.pk)


class TippAdd(LoginRequiredMixin, CreateView):
    model = models.Tipp
    form_class = forms.TippForm

    def form_valid(self, form):
        """Override the form_valid method of the ModelFormMixin to insert
        value of author field. To do this, the form's save() method is
        called with commit=False to be able to edit the new object before
        actually saving it. Additionally, directly upvote the tipp."""
        self.object = form.save(commit=False)
        is_edit = self.object.pk is not None
        self.object.author = self.request.user
        self.object.save()
        if not is_edit:
            # Automatically upvote own tipp
            models.TippVote.objects.create(
                user=self.request.user,
                tipp=self.object,
                vote=True,
            )
        return super().form_valid(form)

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            'Tipp "%s" wurde erfolgreich hinzugefügt.' % self.object.summary,
        )
        return reverse("tipps:tipp_list")


class TippDelete(LoginRequiredMixin, DeleteView):
    model = models.Tipp

    def dispatch(self, request, *args, **kwargs):
        handler = super().dispatch(request, *args, **kwargs)
        # Only allow deletion if current user is owner
        if self.object.author != request.user:
            return HttpResponseForbidden("Du darfst keine fremden Tipps löschen.")
        return handler

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, "Tipp wurde erfolgreich gelöscht."
        )
        messages.add_message(self.request, EVENT, "tipp_delete")
        return reverse("tipps:tipp_list")


class TippVote(LoginRequiredMixin, APIView):
    def post(self, request, pk):
        tipp = get_object_or_404(models.Tipp, pk=pk)
        vote = request.POST.get("vote")

        if vote not in ["up", "down", "remove"]:
            return HttpResponseBadRequest("Expected up/down/remove for vote")

        if vote == "remove":
            models.TippVote.objects.get(user=request.user, tipp=tipp).delete()
        else:
            try:
                vote_obj = models.TippVote.objects.get(user=request.user, tipp=tipp)
            except models.TippVote.DoesNotExist:
                vote_obj = models.TippVote()
                vote_obj.user = request.user
                vote_obj.tipp = tipp
            vote_obj.vote = vote == "up"
            vote_obj.save()

        data = {
            "vote_elem_pk": tipp.pk,
            "vote": vote,
            "vote_count": tipp.TippVote.count(),
            "vote_sum": tipp.vote_sum(),
        }
        return JsonResponse(data)
