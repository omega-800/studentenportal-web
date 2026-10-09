from django.contrib import admin
from django.db.models import Count

from apps.events import models


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "summary",
        "start_date",
        "notifications_sent",
        "notifications_opened",
        "open_rate",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                notifications_sent=Count("notifications"),
                notifications_opened=Count("notifications__opened_at"),
            )
        )

    def notifications_sent(self, obj):
        return obj.notifications_sent

    notifications_sent.short_description = "E-Mails gesendet"

    def notifications_opened(self, obj):
        return obj.notifications_opened

    notifications_opened.short_description = "Geöffnet"

    def open_rate(self, obj):
        if not obj.notifications_sent:
            return "-"
        return "%d %%" % (
            round(100 * obj.notifications_opened / obj.notifications_sent)
        )

    open_rate.short_description = "Öffnungsrate"


@admin.register(models.EventNotification)
class EventNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "sent_at", "opened_at")
    list_filter = ("event",)
    search_fields = ("user__username", "user__email")
    date_hierarchy = "sent_at"
    readonly_fields = ("user", "event", "token", "sent_at", "opened_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
