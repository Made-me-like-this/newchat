# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Room, UserProfile, Video

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'is_private']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input px-4 py-3 rounded-lg border-purple-300 focus:border-purple-500'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-checkbox text-purple-600'})
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-textarea mt-1 block w-full rounded-lg border-purple-300 focus:border-purple-500'}),
            'avatar': forms.FileInput(attrs={'class': 'form-input mt-1 block w-full rounded-lg border-purple-300 focus:border-purple-500'})
        }

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'description', 'file', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input px-4 py-3 rounded-lg border-purple-300 focus:border-purple-500'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea mt-1 block w-full rounded-lg border-purple-300 focus:border-purple-500'}),
            'file': forms.FileInput(attrs={'class': 'form-input mt-1 block w-full rounded-lg border-purple-300 focus:border-purple-500'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-input mt-1 block w-full rounded-lg border-purple-300 focus:border-purple-500'})
        }
