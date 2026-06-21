from django import forms

from apps.tipps import models


class QuoteForm(forms.ModelForm):
    def __init__(self, lecturer_id, *args, **kwargs):
        """This form takes a lecturer_id or None as the first argument.
        If a lecturer id is provided, it will be set as initial value
        for the dropdown."""
        super().__init__(*args, **kwargs)
        if lecturer_id:
            self.fields["lecturer"].initial = lecturer_id

    class Meta:
        model = models.Tipp
        exclude = ("author", "date")
