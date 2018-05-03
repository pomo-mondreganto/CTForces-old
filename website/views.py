from django.shortcuts import render, HttpResponse
from django.views import View

from .models import Post


# Create your views here.

class MainView(View):
    template_name = 'index.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name, context={'posts': Post.objects.all()[:10]})


class UserRegistrationView(View):
    template_name = 'registration.html'

    def get(self, request):
        return render(request=request, template_name=self.template_name)

    def post(self, request):
        return HttpResponse('To be done)))')
