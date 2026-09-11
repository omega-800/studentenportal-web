import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from model_bakery import baker

from apps.events import models
from apps.events.views import _nth_weekday_of_month, add_recurring_events, repeat_dates

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


class TestNthWeekdayOfMonth:
    def test_first_monday_of_january_2026(self):
        # Jan 2026 starts on Thursday, so first Monday is Jan 5
        result = _nth_weekday_of_month(2026, 1, 0, 1)
        assert result == datetime.date(2026, 1, 5)

    def test_second_tuesday_of_march_2026(self):
        # March 2026 starts on Sunday, first Tue is Mar 3, second Tue is Mar 10
        result = _nth_weekday_of_month(2026, 3, 1, 2)
        assert result == datetime.date(2026, 3, 10)

    def test_fifth_monday_does_not_exist(self):
        # Feb 2026 has only 4 Mondays
        result = _nth_weekday_of_month(2026, 2, 0, 5)
        assert result is None

    def test_fourth_friday_of_january_2026(self):
        # Jan 2026: first Fri is Jan 2, 4th Fri is Jan 23
        result = _nth_weekday_of_month(2026, 1, 4, 4)
        assert result == datetime.date(2026, 1, 23)


class TestRepeatDates:
    def test_daily(self):
        start = datetime.date(2026, 1, 1)
        end = datetime.date(2026, 1, 5)
        dates = repeat_dates(start, 1, "day", end)
        assert len(dates) == 5
        assert dates[0] == datetime.date(2026, 1, 1)
        assert dates[-1] == datetime.date(2026, 1, 5)

    def test_every_2_days(self):
        start = datetime.date(2026, 1, 1)
        end = datetime.date(2026, 1, 10)
        dates = repeat_dates(start, 2, "day", end)
        assert dates == [
            datetime.date(2026, 1, 1),
            datetime.date(2026, 1, 3),
            datetime.date(2026, 1, 5),
            datetime.date(2026, 1, 7),
            datetime.date(2026, 1, 9),
        ]

    def test_weekly(self):
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 1, 26)
        dates = repeat_dates(start, 1, "week", end)
        assert dates == [
            datetime.date(2026, 1, 5),
            datetime.date(2026, 1, 12),
            datetime.date(2026, 1, 19),
            datetime.date(2026, 1, 26),
        ]

    def test_biweekly(self):
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 2, 28)
        dates = repeat_dates(start, 2, "week", end)
        assert dates == [
            datetime.date(2026, 1, 5),
            datetime.date(2026, 1, 19),
            datetime.date(2026, 2, 2),
            datetime.date(2026, 2, 16),
        ]

    def test_monthly_weekday_based(self):
        # Jan 5, 2026 is a Monday — it's the 1st Monday of the month
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 4, 30)
        dates = repeat_dates(start, 1, "month", end)
        assert dates == [
            datetime.date(2026, 1, 5),  # 1st Monday of Jan
            datetime.date(2026, 2, 2),  # 1st Monday of Feb
            datetime.date(2026, 3, 2),  # 1st Monday of Mar
            datetime.date(2026, 4, 6),  # 1st Monday of Apr
        ]

    def test_monthly_skips_when_nth_weekday_missing(self):
        # Jan 29, 2026 is Thursday — it's the 5th Thursday
        # Feb 2026 has no 5th Thursday, should skip
        start = datetime.date(2026, 1, 29)
        end = datetime.date(2026, 8, 31)
        dates = repeat_dates(start, 1, "month", end)
        # Only months with a 5th Thursday
        for d in dates:
            assert d.weekday() == 3  # Thursday
            assert (d.day - 1) // 7 + 1 == 5  # 5th occurrence

    def test_every_2_months(self):
        # Jan 13, 2026 is Tuesday — 2nd Tuesday
        start = datetime.date(2026, 1, 13)
        end = datetime.date(2026, 7, 31)
        dates = repeat_dates(start, 2, "month", end)
        assert dates == [
            datetime.date(2026, 1, 13),  # 2nd Tue of Jan
            datetime.date(2026, 3, 10),  # 2nd Tue of Mar
            datetime.date(2026, 5, 12),  # 2nd Tue of May
            datetime.date(2026, 7, 14),  # 2nd Tue of Jul
        ]

    def test_yearly(self):
        # Jan 5, 2026 is 1st Monday of Jan
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2029, 12, 31)
        dates = repeat_dates(start, 1, "year", end)
        assert len(dates) == 4
        assert dates[0] == datetime.date(2026, 1, 5)
        for d in dates:
            assert d.weekday() == 0  # Monday
            assert d.month == 1

    def test_end_date_before_start(self):
        start = datetime.date(2026, 2, 1)
        end = datetime.date(2026, 1, 1)
        for unit in ["day", "week", "month", "year"]:
            dates = repeat_dates(start, 1, unit, end)
            assert dates == [] or dates == []  # month/year include start then break

    def test_same_start_and_end(self):
        d = datetime.date(2026, 5, 1)
        for unit in ["day", "week", "month", "year"]:
            dates = repeat_dates(d, 1, unit, d)
            assert dates == [d]


@pytest.mark.django_db
class TestAddRecurringEvents:
    @patch("apps.events.views.datetime")
    def test_weekly_recurring_creates_copies(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        mock_dt.date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
        user = baker.make(User)
        models.Event.objects.create(
            summary="Weekly Standup",
            description="Team meeting",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            start_time=datetime.time(9, 0),
            end_date=None,
            repeats=True,
            repeat_every=1,
            repeat_unit="week",
            repeat_ends=datetime.date(2026, 1, 26),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        standup_events = [e for e in future if e.summary == "Weekly Standup"]
        assert len(standup_events) == 4

    @patch("apps.events.views.datetime")
    def test_recurring_copies_have_flag(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        mock_dt.date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
        user = baker.make(User)
        models.Event.objects.create(
            summary="Recurring",
            description="Test",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            repeats=True,
            repeat_every=1,
            repeat_unit="week",
            repeat_ends=datetime.date(2026, 1, 19),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        originals = [
            e for e in future if not getattr(e, "is_recurring_instance", False)
        ]
        copies = [e for e in future if getattr(e, "is_recurring_instance", False)]
        assert len(originals) == 1
        assert len(copies) == 2

    @patch("apps.events.views.datetime")
    def test_recurring_preserves_end_date_offset(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        mock_dt.date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
        user = baker.make(User)
        models.Event.objects.create(
            summary="Weekend Event",
            description="Two day event",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            end_date=datetime.date(2026, 1, 7),
            repeats=True,
            repeat_every=1,
            repeat_unit="week",
            repeat_ends=datetime.date(2026, 1, 19),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        events = sorted(
            [e for e in future if e.summary == "Weekend Event"],
            key=lambda e: e.start_date,
        )
        assert len(events) == 3
        for e in events:
            assert e.end_date - e.start_date == datetime.timedelta(days=2)

    @patch("apps.events.views.datetime")
    def test_non_recurring_event_unchanged(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 6, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        mock_dt.date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
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
    def test_monthly_recurring(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 1, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        mock_dt.date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
        user = baker.make(User)
        # Jan 5, 2026 is 1st Monday
        models.Event.objects.create(
            summary="Monthly Meeting",
            description="First Monday",
            author=user,
            start_date=datetime.date(2026, 1, 5),
            repeats=True,
            repeat_every=1,
            repeat_unit="month",
            repeat_ends=datetime.date(2026, 4, 30),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        events = sorted(
            [e for e in future if e.summary == "Monthly Meeting"],
            key=lambda e: e.start_date,
        )
        assert len(events) == 4
        # All should be Mondays
        for e in events:
            assert e.start_date.weekday() == 0

    @patch("apps.events.views.datetime")
    def test_past_recurring_events_in_past_list(self, mock_dt):
        mock_dt.date.today.return_value = datetime.date(2026, 2, 1)
        mock_dt.timedelta = datetime.timedelta
        mock_dt.time = datetime.time
        mock_dt.date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)
        user = baker.make(User)
        models.Event.objects.create(
            summary="Past Recurring",
            description="Already happened",
            author=user,
            start_date=datetime.date(2026, 1, 1),
            repeats=True,
            repeat_every=1,
            repeat_unit="week",
            repeat_ends=datetime.date(2026, 1, 22),
        )
        future, past = add_recurring_events(models.Event.objects.all())
        past_events = [e for e in past if e.summary == "Past Recurring"]
        assert len(past_events) == 4
        assert all(e.start_date < datetime.date(2026, 2, 1) for e in past_events)
