from django import forms

from .models import User, Post


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(max_length=256, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=256, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('User with this email is already registered')
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords did not match')
        return confirm_password

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()

        return user


class PostCreationForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        if not self.user:
            raise Exception('request.user was somehow None')

        super(PostCreationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        post = super(PostCreationForm, self).save(commit=False)
        post.author = self.user

        if commit:
            post.save()

        return post
