"""Shared voting helpers for votable content (quotes, tipps, etc.)."""

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView


def extend_with_votes(queryset, vote_table, fk_column, item_table, user_pk):
    """Extend a queryset with vote annotations using raw SQL.

    Args:
        queryset: The base queryset to annotate.
        vote_table: DB table name for votes (e.g. 'tipps_tippvote').
        fk_column: FK column in vote table pointing to the item (e.g. 'tipp_id').
        item_table: DB table name for items (e.g. 'tipps_tipp').
        user_pk: The current user's PK, or None for anonymous users.
    """
    vote_base_query = (
        "SELECT EXISTS (SELECT id "
        "FROM {vote_table} "
        "WHERE {vote_table}.{fk_column} = {item_table}.id "
        "AND vote = '%s' "
        "AND user_id = %u)"
    ).format(vote_table=vote_table, fk_column=fk_column, item_table=item_table)

    count_query = (
        "SELECT COUNT(*) "
        "FROM {vote_table} "
        "WHERE {vote_table}.{fk_column} = {item_table}.id"
    ).format(vote_table=vote_table, fk_column=fk_column, item_table=item_table)

    count_base_query = count_query + " AND vote = '%s'"

    return queryset.extra(
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


class VoteViewMixin(APIView):
    """Shared vote POST handler for votable models.

    Subclasses must set:
        item_model: The votable model class (e.g. Tipp, Quote)
        vote_model: The vote model class (e.g. TippVote, QuoteVote)
        item_fk_name: The FK field name on the vote model (e.g. 'tipp', 'quote')
    """

    item_model = None
    vote_model = None
    item_fk_name = None

    def post(self, request, pk):
        item = get_object_or_404(self.item_model, pk=pk)
        vote = request.POST.get("vote")

        if vote not in ["up", "down", "remove"]:
            return HttpResponseBadRequest("Expected up/down/remove for vote")

        lookup = {"user": request.user, self.item_fk_name: item}

        if vote == "remove":
            self.vote_model.objects.get(**lookup).delete()
        else:
            try:
                vote_obj = self.vote_model.objects.get(**lookup)
            except self.vote_model.DoesNotExist:
                vote_obj = self.vote_model(**lookup)
            vote_obj.vote = vote == "up"
            vote_obj.save()

        data = {
            "vote_elem_pk": item.pk,
            "vote": vote,
            "vote_count": getattr(item, item.vote_relation).count(),
            "vote_sum": item.vote_sum(),
        }
        return JsonResponse(data)
