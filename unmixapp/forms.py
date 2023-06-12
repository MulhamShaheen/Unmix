from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
import django.forms as forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Feedback


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.password = self.cleaned_data["password1"]
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)


class TrackUploadForm(forms.Form):
    TARGETS = (
        ("BASS", "Bass"),
        ("BEAT", "Drums and percussion"),
        ("VOCAL", "Vocals"),
        ("OTHER", "Others"),
    )

    file = forms.FileField(label="Audio file", max_length=200)
    # target_instrument = forms.SelectMultiple(choices=TARGETS)
    target_instrument = forms.ChoiceField(label="Target instrument", choices=TARGETS)


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["text", "score"]
