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


class UserGeneralUpdateFormWithPassword(forms.ModelForm):
    old_password = forms.CharField(max_length=256, widget=forms.PasswordInput)
    new_password = forms.CharField(max_length=256, widget=forms.PasswordInput)
    new_password2 = forms.CharField(max_length=256, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('avatar', 'email')

    def __init__(self, *args, **kwargs):
        super(UserGeneralUpdateFormWithPassword, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).first()
        if user and user != self.instance:
            raise forms.ValidationError('User with this email is already registered')
        return email

    def clean_old_password(self):
        password = self.cleaned_data['old_password']
        if not self.user.check_password(password):
            raise forms.ValidationError('old password incorrect')
        return password

    def clean_new_password2(self):
        new_password = self.cleaned_data['new_password']
        new_password2 = self.cleaned_data['new_password2']

        if new_password and new_password2 and new_password != new_password2:
            raise forms.ValidationError('Passwords did not match')

        return new_password2

    def save(self, commit=True):
        user = super(UserGeneralUpdateFormWithPassword, self).save(commit=False)
        user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()

        return user


class UserGeneralUpdateFormWithoutPassword(forms.ModelForm):
    class Meta:
        model = User
        fields = ('avatar', 'email')

    def __init__(self, *args, **kwargs):
        super(UserGeneralUpdateFormWithoutPassword, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).first()
        if user and user != self.instance:
            raise forms.ValidationError('User with this email is already registered')
        return email

    def save(self, commit=True):
        user = super(UserGeneralUpdateFormWithoutPassword, self).save(commit=False)
        if commit:
            user.save()

        return user


class UserSocialUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'birth_date', 'country', 'city', 'organization')
