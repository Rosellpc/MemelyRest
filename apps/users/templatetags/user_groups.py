from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    if not user or not hasattr(user, "groups"):
        return False
    return user.groups.filter(name__iexact=group_name).exists()
