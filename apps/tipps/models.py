from datetime import date

from django.conf import settings
from django.db import models


class Tipp(models.Model):
    """A tipp topp tipp."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="Tipp",
        null=True,
        on_delete=models.SET_NULL,
    )
    date = models.DateTimeField(auto_now_add=True)
    summary = models.CharField("Titel", max_length=64)
    description = models.TextField("Beschreibung")

    def date_available(self):
        return self.date != datetime(1970, 1, 1)

    def vote_sum(self):
        """Add up and return all votes for this tipp."""
        up = self.TippVote.filter(vote=True).count()
        down = self.TippVote.filter(vote=False).count()
        return up - down

    def __str__(self):
        return f"{self.summary}"

    class Meta:
        ordering = ["-date"]
        get_latest_by = "date"


class TippVote(models.Model):
    """Tipp votes."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="TippVote",
        null=True,
        on_delete=models.SET_NULL,
    )
    tipp = models.ForeignKey(Tipp, related_name="TippVote", on_delete=models.CASCADE)
    vote = models.BooleanField(help_text="True = upvote, False = downvote")

    def __str__(self):
        fmt_args = self.user.username, "up" if self.vote else "down", self.tipp.pk
        return "User %s votes %s quote %s" % fmt_args

    class Meta:
        unique_together = ("user", "tipp")
