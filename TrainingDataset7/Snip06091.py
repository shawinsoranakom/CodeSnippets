async def aget_user(self, user_id):
        try:
            user = await UserModel._default_manager.aget(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None