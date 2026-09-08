import sys

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.decorators import method_decorator

from apps.front.message_levels import EVENT


class LoginRequiredMixin:
    """Ensures that user must be authenticated in order to access view."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class OwnerDeleteMixin:
    """Delete view mixin that restricts deletion to the object's author."""

    # Subclasses must set these
    owner_field = "author"
    forbidden_message = ""
    success_message = ""
    event_name = ""
    success_url_name = ""

    def dispatch(self, request, *args, **kwargs):
        handler = super().dispatch(request, *args, **kwargs)
        if getattr(self.object, self.owner_field) != request.user:
            return HttpResponseForbidden(self.forbidden_message)
        return handler

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, self.success_message
        )
        messages.add_message(self.request, EVENT, self.event_name)
        return reverse(self.success_url_name)


class AutoUpvoteCreateMixin:
    """CreateView mixin that sets the author and auto-upvotes on creation.

    Subclasses must set:
        vote_model: The vote model class (e.g. TippVote, QuoteVote)
        item_fk_name: The FK field name on the vote model (e.g. 'tipp', 'quote')
    """

    vote_model = None
    item_fk_name = None

    def form_valid(self, form):
        self.object = form.save(commit=False)
        is_edit = self.object.pk is not None
        self.object.author = self.request.user
        self.object.save()
        if not is_edit:
            self.vote_model.objects.create(
                user=self.request.user,
                **{self.item_fk_name: self.object},
                vote=True,
            )
        return super().form_valid(form)


class CommandOutputMixin:
    """Mixin to provide printO and printE methods."""

    def printO(self, msg):
        """Print to stdout. This expects unicode strings!"""
        encoding = self.stdout.encoding or sys.getdefaultencoding()
        self.stdout.write(msg.encode(encoding, "replace"))

    def printE(self, msg):
        """Print to stderr. This expects unicode strings!"""
        encoding = self.stderr.encoding or sys.getdefaultencoding()
        self.stderr.write(msg.encode(encoding, "replace"))
