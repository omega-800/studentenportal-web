import copy
import datetime
from urllib.parse import urlsplit, urlunsplit

import vobject
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from apps.events import forms, models
from apps.front.mixins import LoginRequiredMixin


class Event(DetailView):
    model = models.Event


class EventAdd(LoginRequiredMixin, CreateView):
    model = models.Event
    form_class = forms.EventForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            'Event "%s" wurde erfolgreich erstellt.' % self.object.summary,
        )
        return HttpResponseRedirect(
            reverse("events:event_detail", args=[self.object.pk])
        )


class EventEdit(LoginRequiredMixin, UpdateView):
    model = models.Event
    form_class = forms.EventForm

    def dispatch(self, request, *args, **kwargs):
        handler = super().dispatch(request, *args, **kwargs)
        # Only allow editing if current user is owner
        if self.object.author != request.user:
            return HttpResponseForbidden("Du darfst keine fremden Events editieren.")
        return handler

    def get_success_url(self):
        return reverse("events:event_detail", args=[self.object.pk])


class EventDelete(LoginRequiredMixin, DeleteView):
    model = models.Event

    def dispatch(self, request, *args, **kwargs):
        handler = super().dispatch(request, *args, **kwargs)
        # Only allow deletion if current user is owner
        if self.object.author != request.user:
            return HttpResponseForbidden("Du darfst keine fremden Events löschen.")
        return handler

    def get_success_url(self):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            'Event "%s" wurde erfolgreich gelöscht.' % self.object.summary,
        )
        return reverse("events:event_list")


def repeat_dates(start_date, interval_days, end_date):
    dates = []
    d = start_date
    while d <= end_date:
        dates.append(d)
        d = d + datetime.timedelta(days=interval_days)
    return dates


def add_recurring_events(events):
    future = []
    past = []
    for e in events:
        if e.start_date > datetime.date.today():
            future.append(e)
        else:
            past.append(e)
        if (
            e.repeats
            and e.repeat_days is not None
            and e.repeat_days > 0
            and e.repeat_ends is not None
        ):
            dates = repeat_dates(e.start_date, e.repeat_days, e.repeat_ends)
            for date in dates[1:]:
                new_e = copy.copy(e)
                new_e.start_date = date
                new_e.end_date = (
                    date + (e.start_date - e.end_date)
                    if e.end_date is not None
                    else None
                )
                if date > datetime.date.today():
                    future.append(new_e)
                else:
                    past.append(new_e)
    return sorted(
        future, key=lambda e: (e.start_date, e.start_time or datetime.time.min)
    ), sorted(
        past,
        key=lambda e: (-e.start_date.toordinal(), e.start_time or datetime.time.min),
    )


class EventList(TemplateView):
    template_name = "events/event_list.html"

    def get_context_data(self, **kwargs):
        model = models.Event
        context = super().get_context_data(**kwargs)

        future, past = add_recurring_events(model.objects.all())

        context["events_future"] = future
        # TODO: let user input the timeframe
        context["events_past"] = [
            e
            for e in past
            if e.start_date > datetime.date.today() - relativedelta(years=10)
        ]
        http_url = self.request.build_absolute_uri(reverse("events:event_calendar"))
        context["current_year"] = datetime.date.today().year
        context["webcal_url"] = urlunsplit(urlsplit(http_url)._replace(scheme="webcal"))
        return context


class EventCalendar(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, *args, **kwargs):
        cal = vobject.iCalendar()
        cal.add("x-wr-calname").value = "Studentenportal Events"
        cal.add("x-wr-timezone").value = "Europe/Zurich"

        future, past = add_recurring_events(models.Event.objects.all())

        for event in reversed(future + past):
            vevent = cal.add("vevent")
            vevent.add("summary").value = event.summary
            vevent.add("description").value = event.description
            if event.start_time:
                dtstart = datetime.datetime.combine(event.start_date, event.start_time)
            else:
                dtstart = event.start_date
            vevent.add("dtstart").value = dtstart
            if event.end_date or event.end_time:
                if not event.end_date:
                    dtend = datetime.datetime.combine(event.start_date, event.end_time)
                elif event.end_time:
                    dtend = datetime.datetime.combine(event.end_date, event.end_time)
                else:
                    dtend = datetime.datetime.combine(
                        event.end_date, datetime.time(23, 59, 59)
                    )
                vevent.add("dtend").value = dtend
            if event.author:
                vevent.add("comment").value = "Erfasst von %s" % event.author.name()
        return HttpResponse(cal.serialize(), content_type="text/calendar")
