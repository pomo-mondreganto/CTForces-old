from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, Post, Comment, Task, File, Contest


class RegistrationForm(forms.ModelForm):
    username = forms.CharField(validators=[User.username_validator], required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(max_length=256, widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            self.add_error(field='email', error='User with this email is already registered.')

        return email

    def clean_password2(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']

        if password1 != password2:
            self.add_error(field='password2', error='Passwords did not match.')

        return password2

    def clean_password1(self):
        password1 = self.cleaned_data['password1']

        try:
            validate_password(password=password1)
        except ValidationError as e:
            for message in e:
                self.add_error(field='password1', error=message)

        return password1

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False

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


class UserGeneralUpdateForm(forms.ModelForm):
    old_password = forms.CharField(max_length=256, widget=forms.PasswordInput, required=False)
    new_password = forms.CharField(max_length=256, widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(max_length=256, widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def __init__(self, *args, **kwargs):
        super(UserGeneralUpdateForm, self).__init__(*args, **kwargs)

    # def clean_email(self):
    #     email = self.cleaned_data['email']
    #     user = User.objects.filter(email=email).first()
    #
    #     if user and user != self.instance:
    #         self.add_error(field='email', error='User with this email is already registered.')
    #
    #     return email

    def clean_old_password(self):
        if not self.cleaned_data.get('old_password'):
            return ''

        password = self.cleaned_data['old_password']

        if not self.instance.check_password(password):
            self.add_error(field='old_password', error='Old password entered incorrectly.')

        return password

    def clean_new_password(self):
        if not self.cleaned_data.get('new_password'):
            return ''

        new_password = self.cleaned_data['new_password']

        try:
            validate_password(password=new_password)
        except ValidationError as e:
            for message in e:
                self.add_error(field='new_password', error=message)

        return new_password

    def clean(self):
        super(UserGeneralUpdateForm, self).clean()

        if self.cleaned_data.get('new_password'):
            new_password = self.cleaned_data['new_password']
            old_password = self.cleaned_data.get('old_password')
            new_password2 = self.cleaned_data.get('new_password2')
            if not old_password:
                self.add_error(field='old_password', error='You need to enter old password in order to change it.')
            if new_password != new_password2:
                self.add_error(field='new_password2', error='Passwords did not match.')

    def save(self, commit=True):
        user = super(UserGeneralUpdateForm, self).save(commit=False)
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])

        if commit:
            user.save()

        return user


class UserSocialUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'birth_date', 'country', 'city', 'organization')


class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('avatar',)


class CommentCreationForm(forms.ModelForm):
    post_id = forms.IntegerField(required=True)
    parent_id = forms.IntegerField(required=False)

    class Meta:
        model = Comment
        fields = ('text', 'image')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')

        if not self.user:
            raise Exception('User is None in comment creation')

        super(CommentCreationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        comment = super(CommentCreationForm, self).save(commit=False)

        comment.post_id = self.cleaned_data['post_id']
        comment.parent_id = self.cleaned_data.get('parent_id')
        comment.author = self.user

        if commit:
            comment.save()

        return comment


class TaskForm(forms.ModelForm):
    cost = forms.IntegerField(min_value=1, max_value=9999)

    class Meta:
        model = Task
        fields = ('name', 'description', 'flag', 'cost', 'is_published')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        if not self.user:
            raise Exception('request.user was somehow None')

        super(TaskForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        task = super(TaskForm, self).save(commit=False)
        task.author = self.user

        if commit:
            task.save()

        return task


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('file_field',)


class TaskTagForm(forms.Form):
    name = forms.CharField(max_length=15)


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ('title', 'description', 'start_time', 'end_time')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        if not self.user:
            raise Exception('request.user was somehow None')

        super(ContestForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        contest = super(ContestForm, self).save(commit=False)
        contest.author = self.user

        if commit:
            contest.save()

        return contest
