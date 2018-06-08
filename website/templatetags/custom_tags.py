from django import template

register = template.Library()


@register.filter
def get_type(value):
    return type(value)


@register.filter
def is_friends_with(user, other_user):
    return user and other_user and user.friends.filter(id=other_user.id).exists()
