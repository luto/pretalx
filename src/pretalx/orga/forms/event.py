from django import forms
from django.utils.timezone import get_current_timezone_name

from pretalx.common.forms import ReadOnlyFlag
from pretalx.event.models import Event
from pretalx.person.models import EventPermission, User


class EventForm(ReadOnlyFlag, forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(queryset=User.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['timezone'] = get_current_timezone_name()

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        qs = Event.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(slug__iexact=slug).exists():
            raise forms.ValidationError('This slug is already taken.')
        return slug.lower()

    def _save_m2m(self):
        new_users = set(self.cleaned_data['permissions'])
        old_users = set(User.objects.filter(permissions__event=self.instance, permissions__is_orga=True))

        to_be_removed = old_users - new_users
        to_be_added = new_users - old_users

        for user in to_be_removed:
            EventPermission.objects.get(user=user, event=self.instance, is_orga=True).delete()

        for user in to_be_added:
            EventPermission.objects.create(user=user, event=self.instance, is_orga=True)

    class Meta:
        model = Event
        fields = [
            'name', 'slug', 'subtitle', 'is_public', 'date_from', 'date_to',
            'timezone', 'email', 'color', 'permissions',
        ]