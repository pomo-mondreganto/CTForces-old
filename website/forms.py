from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, Post, Comment, Task, File


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
        fields = ('email', 'avatar')

    def __init__(self, *args, **kwargs):
        super(UserGeneralUpdateForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if user and user != self.instance:
            self.add_error(field='email', error='User with this email is already registered.')

        return email

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
    parent_id = forms.IntegerField(required=False)

    class Meta:
        model = Comment
        fields = ('post', 'text', 'image')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')

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
            parent = Comment.objects.get(id=self.cleaned_data['parent_id'])
        comment.parent = parent
        comment.author = self.user
        if commit:
            comment.save()

        return comment


class TaskCreationForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('name', 'description', 'flag', 'cost')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        if not self.user:
            raise Exception('request.user was somehow None')

        super(TaskCreationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        task = super(TaskCreationForm, self).save(commit=False)
        task.author = self.user

        if commit:
            task.save()

        return task


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('file_field',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.task = kwargs.pop('task', None)

        if not self.user:
            raise Exception('User not provided')

        if not self.task:
            raise Exception('Task not provided')

        super(FileUploadForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        file = super(FileUploadForm, self).save(commit=False)
        file.owner = self.user
        file.task = self.task

        if commit:
            file.save()

        return file
