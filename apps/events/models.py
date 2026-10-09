from datetime import date

from django.conf import settings
from django.db import models


def picture_file_name(instance, filename):
    """Where to put a newly uploaded picture."""
    return "/".join(["event_pictures", str(instance.start_date.year), filename])


class Event(models.Model):
    """An event.
    If end_date is null, then assume end_date = start_date.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="Event",
        null=True,
        on_delete=models.SET_NULL,
    )
    summary = models.CharField("Titel", max_length=64)
    description = models.TextField("Beschreibung")
    start_date = models.DateField("Startdatum", help_text="Format: dd.mm.YYYY")
    start_time = models.TimeField(
        "Startzeit", null=True, blank=True, help_text="Format: hh:mm"
    )
    end_date = models.DateField(
        "Enddatum", null=True, blank=True, help_text="Format: dd.mm.YYYY"
    )
    end_time = models.TimeField(
        "Endzeit", null=True, blank=True, help_text="Format: hh:mm"
    )

    REPEAT_UNIT_CHOICES = [
        ("day", "Tage"),
        ("week", "Wochen"),
        ("month", "Monate"),
        ("year", "Jahre"),
    ]

    repeats = models.BooleanField(
        "Wiederholend",
        null=False,
        default=False,
        help_text="Ob sich das Event wiederholt",
    )
    repeat_every = models.PositiveSmallIntegerField(
        "Alle",
        null=True,
        blank=True,
        help_text="Intervall der Wiederholung (z.B. 2 für alle 2 Wochen)",
    )
    repeat_unit = models.CharField(
        "Einheit",
        max_length=5,
        null=True,
        blank=True,
        choices=REPEAT_UNIT_CHOICES,
        help_text="Einheit der Wiederholung",
    )
    repeat_ends = models.DateField(
        "Wiederholungsende", null=True, blank=True, help_text="Format: dd.mm.YYYY"
    )

    location = models.CharField(
        "Ort",
        max_length=80,
        null=True,
        blank=True,
        help_text='Veranstaltungsort, zB "Gebäude 3" oder "Bären Rapperswil"',
    )
    url = models.URLField(
        "URL", null=True, blank=True, help_text="URL zu Veranstaltungs-Website"
    )
    picture = models.ImageField(
        "Bild/Flyer",
        upload_to=picture_file_name,
        null=True,
        blank=True,
        help_text="Bild oder Flyer",
    )

    def notification_stats(self):
        """Number of e-mail notifications sent for this event, how many
        were opened (via the tracking pixel) and the open rate in percent."""
        sent = self.notifications.count()
        opened = self.notifications.filter(opened_at__isnull=False).count()
        return {
            "sent": sent,
            "opened": opened,
            "rate": round(100 * opened / sent) if sent else None,
        }

    def is_over(self):
        """Return whether the start_date has already passed or not.
        On the start_date day itself, is_over() will return False."""
        delta = self.start_date - date.today()
        return delta.days < 0

    def all_day(self):
        """Return whether the event runs all day long.
        This is the case if start_time and end_time are not set."""
        return self.start_time is None and self.end_time is None

    def days_until(self):
        """Return how many days are left until the day of the event."""
        delta = self.start_date - date.today()
        return delta.days if delta.days > 0 else None

    def __str__(self):
        return f"{self.start_date} {self.summary}"


class EventNotification(models.Model):
    """A notification e-mail that was sent about an event to a single user.

    ``opened_at`` is set when the tracking pixel in the e-mail was loaded,
    i.e. when the user (probably) opened the e-mail.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="event_notifications",
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey(
        Event, related_name="notifications", on_delete=models.CASCADE
    )
    token = models.CharField(max_length=64, unique=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_opened(self):
        return self.opened_at is not None

    def pixel_url(self):
        from django.conf import settings as django_settings

        from django.urls import reverse

        return "%s%s" % (
            django_settings.SITE_URL,
            reverse("events:event_notification_pixel", args=[self.token]),
        )

    def __str__(self):
        return f"{self.user} / {self.event}"
