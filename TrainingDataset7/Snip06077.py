def _get_group_permissions(self, user_obj):
        return Permission.objects.filter(group__in=user_obj.groups.all())