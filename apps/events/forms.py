from django import forms

from apps.events import models


class EventForm(forms.ModelForm):
    class Meta:
        model = models.Event
        exclude = ("author",)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("repeats") and (
            cleaned_data.get("repeat_days") is None
            or cleaned_data.get("repeat_days") <= 0
            or cleaned_data.get("repeat_ends") is None
        ):
            raise forms.ValidationError(
                'Für wiederholende Events müssen "Tage" (>0) und "Wiederholungsende" angegeben werden.'
            )
        return cleaned_data
