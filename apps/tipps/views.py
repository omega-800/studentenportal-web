from django.contrib import messages
from django.urls import reverse
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from apps.front.mixins import AutoUpvoteCreateMixin, LoginRequiredMixin, OwnerDeleteMixin
from apps.front.voting import VoteViewMixin, extend_with_votes
from apps.tipps import forms, models


class TippList(ListView):
    paginate_by = 50

    def get_queryset(self):
        return extend_with_votes(
            models.Tipp.objects.all(),
            "tipps_tippvote", "tipp_id", "tipps_tipp",
            self.request.user.pk,
        )


class TippAdd(LoginRequiredMixin, AutoUpvoteCreateMixin, CreateView):
    model = models.Tipp
    form_class = forms.TippForm
    vote_model = models.TippVote
    item_fk_name = "tipp"

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            'Tipp "%s" wurde erfolgreich hinzugefügt.' % self.object.summary,
        )
        return reverse("tipps:tipp_list")


class TippDelete(LoginRequiredMixin, OwnerDeleteMixin, DeleteView):
    model = models.Tipp
    forbidden_message = "Du darfst keine fremden Tipps löschen."
    success_message = "Tipp wurde erfolgreich gelöscht."
    event_name = "tipp_delete"
    success_url_name = "tipps:tipp_list"


class TippVote(LoginRequiredMixin, VoteViewMixin):
    item_model = models.Tipp
    vote_model = models.TippVote
    item_fk_name = "tipp"
