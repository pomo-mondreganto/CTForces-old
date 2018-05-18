from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, Post, Comment


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            self.add_error(field='email', error='User with this email is already registered.')

        return email

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']

        if password != confirm_password:
            self.add_error(field='confirm_password', error='Passwords did not match.')

        return confirm_password

    def clean_password(self):
        password = self.cleaned_data['password']

        try:
            validate_password(password=password)
        except ValidationError as e:
            for message in e:
                self.add_error(field='password', error=message)

        return password

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
    old_password = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)
    new_password = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)
    new_password2 = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ('avatar', 'email')

    def __init__(self, *args, **kwargs):
        super(UserGeneralUpdateFormWithPassword, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if user and user != self.instance:
            self.add_error(field='email', error='User with this email is already registered.')

        return email

    def clean_old_password(self):
        password = self.cleaned_data['old_password']

        if not self.instance.check_password(password):
            self.add_error(field='old_password', error='Old password entered incorrectly.')

        return password

    def clean_new_password(self):
        new_password = self.cleaned_data['new_password']

        try:
            validate_password(password=new_password)
        except ValidationError as e:
            for message in e:
                self.add_error(field='new_password', error=message)

        return new_password

    def clean_new_password2(self):
        new_password = self.cleaned_data['new_password']
        new_password2 = self.cleaned_data['new_password2']

        if new_password != new_password2:
            self.add_error(field='new_password2', error='Passwords did not match.')

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
            self.add_error(field='email', error='User with this email is already registered.')

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


class CommentCreationForm(forms.ModelForm):
    parent_id = forms.IntegerField(required=False)

    class Meta:
        model = Comment
        fields = ('post', 'text', 'image')

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')

        self.user = User.objects.get(id=user_id)
        if not self.user:
            raise Exception('User is None in comment creation')

        super(CommentCreationForm, self).__init__(*args, **kwargs)

    def clean_parent_id(self):
        parent_id = self.cleaned_data.get('parent_id')
        if not parent_id:
            return None
        comment = Comment.objects.get(id=parent_id)
        if not comment:
            self.add_error(field='parent_id', error='No such comment')
        return parent_id

    def save(self, commit=True):
        comment = super(CommentCreationForm, self).save(commit=False)
        parent = None
        if self.cleaned_data.get('parent_id'):
            parent = Comment.objects.get(id=self.cleaned_data.get('parent_id'))
        comment.parent = parent
        comment.author = self.user
        if commit:
            comment.save()

        return comment
