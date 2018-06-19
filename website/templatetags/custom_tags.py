from django import template

register = template.Library()


@register.filter
def get_type(value):
    return type(value)


@register.filter
def is_friends_with(user, other_user):
    return not user.is_anonymous and not other_user.is_anonymous and user.friends.filter(id=other_user.id).exists()


def is_in_m2m(obj, obj_set):
    return obj_set.filter(id=obj.id).exists()
