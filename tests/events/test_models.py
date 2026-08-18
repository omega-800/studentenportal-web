import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from model_bakery import baker

from apps.events import models
from apps.events.views import add_recurring_events, repeat_dates

User = get_user_model()


@pytest.mark.django_db
class TestEventModel:
    def test_date_time_event(self):
        user = baker.make(User, username="testuser")
        event = models.Event.objects.create(
            summary="Testbar",
            description="This is a bar where people drink and party to \
                          test the studentenportal event feature.",
            author=user,
            start_date=datetime.date(day=1, month=9, year=2010),
            start_time=datetime.time(hour=19, minute=30),
            end_time=datetime.time(hour=23, minute=59),
        )

        assert event.summary == "Testbar"
        assert event.end_date is None
        assert event.author.username == "testuser"
        assert event.is_over()
        assert event.days_until() is None

    def test_all_day_event(self):
        user = baker.make(User)
        start_date = datetime.date.today() + datetime.timedelta(days=365)
        event = models.Event.objects.create(
            summary="In a year",
            description="This happens in a year from now.",
            author=user,
            start_date=start_date,
            end_date=start_date + datetime.timedelta(days=1),
        )

        assert event.summary == "In a year"
        assert event.start_time is None
        assert event.end_time is None
        assert not event.is_over()
        assert event.all_day()
        assert event.days_until() == 365

    def test_null_value_author(self):
        event = models.Event()
        event.summary = "Testbar"
        event.description = "Dies ist eine bar deren autor nicht mehr existiert."
        event.author = None
        event.start_date = datetime.date(day=1, month=9, year=2010)
        event.start_time = datetime.time(hour=19, minute=30)
        event.end_time = datetime.time(hour=23, minute=59)
        try:
            event.save()
        except IntegrityError:
            pytest.fail("An event with no author should not throw an IntegrityError.")


class TestRepeatDates:
    def test_basic_weekly(self):
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 1, 26)
        dates = repeat_dates(start, 7, end)
        assert dates == [
            datetime.date(2026, 1, 5),
            datetime.date(2026, 1, 12),
            datetime.date(2026, 1, 19),
            datetime.date(2026, 1, 26),
        ]

    def test_end_date_between_intervals(self):
        start = datetime.date(2026, 1, 1)
        end = datetime.date(2026, 1, 10)
        dates = repeat_dates(start, 7, end)
        assert dates == [
            datetime.date(2026, 1, 1),
            datetime.date(2026, 1, 8),
        ]

    def test_end_date_before_start(self):
        start = datetime.date(2026, 2, 1)
        end = datetime.date(2026, 1, 1)
        dates = repeat_dates(start, 7, end)
        assert dates == []

    def test_single_day_interval(self):
        start = datetime.date(2026, 3, 1)
        end = datetime.date(2026, 3, 3)
        dates = repeat_dates(start, 1, end)
        assert len(dates) == 3

    def test_same_start_and_end(self):
        d = datetime.date(2026, 5, 1)
        dates = repeat_dates(d, 7, d)
        assert dates == [d]


@pytest.mark.django_db
class TestAddRecurringEvents:
    @patch("apps.events.views.datetime")
    def test_recurring_creates_copies(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        user = baker.make(User)
        event = models.Event.objects.create(
            summary="Weekly Standup",
            description="Team meeting",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            start_time=datetime.time(9, 0),
            end_date=None,
            repeats=True,
            repeat_days=7,
            repeat_ends=datetime.date(2026, 1, 26),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        standup_events = [e for e in future if e.summary == "Weekly Standup"]
        assert len(standup_events) == 4
        dates = [e.start_date for e in standup_events]
        assert dates == [
            datetime.date(2026, 1, 5),
            datetime.date(2026, 1, 12),
            datetime.date(2026, 1, 19),
            datetime.date(2026, 1, 26),
        ]

    @patch("apps.events.views.datetime")
    def test_recurring_copies_have_flag(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        user = baker.make(User)
        models.Event.objects.create(
            summary="Recurring",
            description="Test",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            repeats=True,
            repeat_days=7,
            repeat_ends=datetime.date(2026, 1, 19),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        originals = [e for e in future if not getattr(e, "is_recurring_instance", False)]
        copies = [e for e in future if getattr(e, "is_recurring_instance", False)]
        assert len(originals) == 1
        assert len(copies) == 2

    @patch("apps.events.views.datetime")
    def test_recurring_preserves_end_date_offset(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        user = baker.make(User)
        models.Event.objects.create(
            summary="Weekend Event",
            description="Two day event",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            end_date=datetime.date(2026, 1, 7),
            repeats=True,
            repeat_days=7,
            repeat_ends=datetime.date(2026, 1, 19),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        events = sorted(
            [e for e in future if e.summary == "Weekend Event"],
            key=lambda e: e.start_date,
        )
        assert len(events) == 3
        # Each copy should preserve the 2-day duration
        for e in events:
            assert e.end_date - e.start_date == datetime.timedelta(days=2)

    @patch("apps.events.views.datetime")
    def test_non_recurring_event_unchanged(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 6, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        user = baker.make(User)
        models.Event.objects.create(
            summary="One-off",
            description="Single event",
            author=user,
            start_date=datetime.date(2026, 6, 15),
            repeats=False,
        )
        future, past = add_recurring_events(models.Event.objects.all())
        assert len(future) == 1
        assert future[0].summary == "One-off"
        assert not getattr(future[0], "is_recurring_instance", False)

    @patch("apps.events.views.datetime")
    def test_past_recurring_events_in_past_list(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 2, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        user = baker.make(User)
        models.Event.objects.create(
            summary="Past Recurring",
            description="Already happened",
            author=user,
            start_date=datetime.date(2026, 1, 1),
            repeats=True,
            repeat_days=7,
            repeat_ends=datetime.date(2026, 1, 22),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        past_events = [e for e in past if e.summary == "Past Recurring"]
        assert len(past_events) == 4
        assert all(e.start_date < datetime.date(2026, 2, 1) for e in past_events)
