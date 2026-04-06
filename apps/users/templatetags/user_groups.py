from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    if not user or not hasattr(user, "groups"):
        return False
    return user.groups.filter(name__iexact=group_name).exists()


@register.filter
def user_initials(user):
    if not user:
        return ""
    if getattr(user, "first_name", "") or getattr(user, "last_name", ""):
        first = (user.first_name or "").strip()[:1]
        last = (user.last_name or "").strip()[:1]
        return f"{first}{last}".upper() or (user.username or "")[:2].upper()
    return (user.username or "")[:2].upper()
