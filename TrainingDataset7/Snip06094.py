async def aauthenticate(self, request, remote_user):
        """See authenticate()."""
        if not remote_user:
            return
        created = False
        user = None
        username = self.clean_username(remote_user)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = await UserModel._default_manager.aget_or_create(
                **{UserModel.USERNAME_FIELD: username}
            )
        else:
            try:
                user = await UserModel._default_manager.aget_by_natural_key(username)
            except UserModel.DoesNotExist:
                pass
        user = await self.aconfigure_user(request, user, created=created)
        return user if self.user_can_authenticate(user) else None