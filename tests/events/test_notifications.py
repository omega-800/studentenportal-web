import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from model_bakery import baker

from apps.events import models

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_mail():
    mail.outbox.clear()
    yield


def create_event(summary="Test Event"):
    return models.Event.objects.create(
        summary=summary,
        description="A new event",
        start_date=datetime.date.today() + datetime.timedelta(days=1),
        start_time=datetime.time(16, 0),
        end_time=datetime.time(18, 0),
        location="Gebäude 1",
    )


@pytest.mark.django_db
def test_event_notification_sent_to_opted_in_users():
    """New events are announced by e-mail to all opted-in users, on their
    main and their additional notification address."""
    baker.make(
        User,
        username="notify.me",
        email="notify@ost.ch",
        notification_email="extra@ost.ch",
    )
    baker.make(
        User,
        username="nope.me",
        email="nope@ost.ch",
        receive_event_notifications=False,
    )

    create_event()

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert set(message.to) == {"notify@ost.ch", "extra@ost.ch"}
    assert "Test Event" in message.subject
    assert "Test Event" in message.body
    assert "Gebäude 1" in message.body
    assert "https://studentenportal.ch/profil/" in message.body


@pytest.mark.django_db
def test_event_notification_single_email_for_same_address():
    """A user whose notification address equals their main address only
    gets one e-mail."""
    baker.make(
        User,
        username="twice.me",
        email="twice@ost.ch",
        notification_email="TWICE@ost.ch",
    )

    create_event()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["twice@ost.ch"]


@pytest.mark.django_db
def test_event_notification_personalized_per_user():
    """Each opted-in user gets their own e-mail, addressed by their name."""
    baker.make(
        User,
        username="anna.ann",
        first_name="Anna",
        last_name="Ann",
        email="anna@ost.ch",
    )
    baker.make(
        User,
        username="ben.ben",
        first_name="Ben",
        last_name="Ben",
        email="ben@ost.ch",
    )

    create_event()

    assert len(mail.outbox) == 2
    by_recipient = {message.to[0]: message for message in mail.outbox}
    assert set(by_recipient) == {"anna@ost.ch", "ben@ost.ch"}
    assert "Hey Anna Ann," in by_recipient["anna@ost.ch"].body
    assert "Hey Ben Ben," in by_recipient["ben@ost.ch"].body
    assert "Hey Anna Ann," not in by_recipient["ben@ost.ch"].body
    assert "Hey Ben Ben," not in by_recipient["anna@ost.ch"].body


@pytest.mark.django_db
def test_event_notification_falls_back_to_username():
    """Users without a first/last name are addressed by their username."""
    baker.make(User, username="noname.user", email="noname@ost.ch")

    create_event()

    assert len(mail.outbox) == 1
    assert "Hey noname.user," in mail.outbox[0].body


@pytest.mark.django_db
def test_event_notification_has_tracking_pixel():
    """The e-mail is sent as multipart and the HTML part contains the
    tracking pixel with the per-user token."""
    baker.make(User, username="pixel.me", email="pixel@ost.ch")

    event = create_event()

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert "multipart/alternative" in message.message().as_string()
    html_parts = [
        part for part, mimetype in message.alternatives if mimetype == "text/html"
    ]
    assert len(html_parts) == 1
    notification = models.EventNotification.objects.get(
        event=event, user__username="pixel.me"
    )
    assert notification.token in html_parts[0]
    assert (
        'src="https://studentenportal.ch/events/notification-pixel/%s/"'
        % (notification.token)
        in html_parts[0]
    )
    assert "Test Event" in html_parts[0]
    # The plain-text part must not contain the pixel
    assert notification.token not in message.body


@pytest.mark.django_db
def test_event_notification_one_row_per_user():
    baker.make(User, username="a.user", email="a@ost.ch")
    baker.make(User, username="b.user", email="b@ost.ch")
    baker.make(
        User, username="c.user", email="c@ost.ch", receive_event_notifications=False
    )

    event = create_event()

    assert models.EventNotification.objects.filter(event=event).count() == 2
    tokens = set(
        models.EventNotification.objects.filter(event=event).values_list(
            "token", flat=True
        )
    )
    assert len(tokens) == 2


@pytest.mark.django_db
def test_event_notification_not_sent_when_disabled():
    baker.make(User, username="notify.me", email="notify@ost.ch")

    with override_settings(EVENT_NOTIFICATIONS_ENABLED=False):
        create_event()

    assert mail.outbox == []


@pytest.mark.django_db
def test_event_notification_no_recipients_no_email():
    baker.make(
        User,
        username="nope.me",
        email="nope@ost.ch",
        receive_event_notifications=False,
    )

    create_event()

    assert mail.outbox == []


@pytest.mark.django_db
def test_event_edit_does_not_notify():
    """Only new events are announced, not edits of existing ones."""
    baker.make(User, username="notify.me", email="notify@ost.ch")

    event = create_event()
    assert len(mail.outbox) == 1

    event.summary = "Changed"
    event.save()

    assert len(mail.outbox) == 1
