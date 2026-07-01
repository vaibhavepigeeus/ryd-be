from users.models import Users


def get_user_from_request(request):
    user = getattr(request, "user", None)
    if user and isinstance(user, Users):
        return user

    user_id = request.COOKIES.get("userId")
    if not user_id:
        return None

    try:
        return Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return None
