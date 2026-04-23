def get_user(self, user_id):
        try:
            return CustomUser.custom_objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None