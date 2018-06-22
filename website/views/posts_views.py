from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from website.decorators import custom_login_required as login_required
from website.forms import PostCreationForm, CommentCreationForm
from website.mixins import PermissionsRequiredMixin
from website.models import Post, User


@require_POST
@login_required
def leave_comment(request):
    parent_id = request.POST.get('parent_id')
    form = CommentCreationForm(request.POST, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'comment added successfully')
    else:
        for field in form.errors:
            for error in form.errors[field]:
                extra_tags = [field]
                if parent_id:
                    extra_tags.append(str(parent_id))
                else:
                    extra_tags.append('top')
                messages.error(request, error, extra_tags=extra_tags)
        print(form.errors)

    if not request.POST.get('post_id'):
        return redirect('main_view')
    return redirect('post_view', post_id=request.POST['post_id'])


class UserBlogView(TemplateView):
    template_name = 'user_blog.html'

    def get_context_data(self, **kwargs):
        context = super(UserBlogView, self).get_context_data(**kwargs)
        username = kwargs.get('username')
        page = kwargs.get('page', 1)
        user = User.objects.filter(username=username).annotate(post_count=Count('posts')).first()
        if not user:
            raise Http404()

        posts = user.posts.all().order_by('-created').select_related('author')[(page - 1) * 10: page * 10]
        page_count = (user.post_count + settings.POSTS_ON_PAGE - 1) // settings.POSTS_ON_PAGE
        context['user'] = user
        context['page'] = page
        context['posts'] = posts
        context['page_count'] = page_count
        return context


class PostCreationView(PermissionsRequiredMixin, TemplateView):
    template_name = 'create_post.html'

    permissions_required = (
        'add_post',
    )

    @staticmethod
    def post(request):

        form = PostCreationForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'post added successfully')
            return redirect('user_blog_view', username=request.user.username)
        else:
            print(form.errors)

            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error, extra_tags=field)

            return redirect('post_creation_view')


class PostView(TemplateView):
    template_name = 'post_view.html'

    def get_context_data(self, **kwargs):
        context = super(PostView, self).get_context_data(**kwargs)
        post_id = kwargs.get('post_id')
        post = Post.objects.filter(id=post_id).prefetch_related('comments', 'author').first()

        if not post:
            raise Http404()

        context['post'] = post
        context['user'] = post.author
        return context
