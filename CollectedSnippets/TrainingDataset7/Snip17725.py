def sync_test_func(user):
            return bool(
                models.Group.objects.filter(name__istartswith=user.username).exists()
            )