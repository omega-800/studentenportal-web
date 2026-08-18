from django.db import migrations, models


def convert_repeat_days(apps, schema_editor):
    """Convert repeat_days to repeat_every + repeat_unit."""
    Event = apps.get_model("events", "Event")
    for event in Event.objects.filter(repeats=True, repeat_days__isnull=False):
        days = event.repeat_days
        if days % 365 == 0:
            event.repeat_every = days // 365
            event.repeat_unit = "year"
        elif days % 30 == 0:
            event.repeat_every = days // 30
            event.repeat_unit = "month"
        elif days % 7 == 0:
            event.repeat_every = days // 7
            event.repeat_unit = "week"
        else:
            event.repeat_every = days
            event.repeat_unit = "day"
        event.save(update_fields=["repeat_every", "repeat_unit"])


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_event_repeat_days_event_repeat_ends_event_repeats"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="repeat_every",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Intervall der Wiederholung (z.B. 2 für alle 2 Wochen)",
                null=True,
                verbose_name="Alle",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="repeat_unit",
            field=models.CharField(
                blank=True,
                choices=[
                    ("day", "Tage"),
                    ("week", "Wochen"),
                    ("month", "Monate"),
                    ("year", "Jahre"),
                ],
                help_text="Einheit der Wiederholung",
                max_length=5,
                null=True,
                verbose_name="Einheit",
            ),
        ),
        migrations.RunPython(convert_repeat_days, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="event",
            name="repeat_days",
        ),
    ]
