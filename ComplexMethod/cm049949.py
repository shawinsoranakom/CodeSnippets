def is_current_user(self, env):
            """Return whether the current target is the current user or guest of the given env.
            If there is no target at all, this is always True."""
            if self.channel is None and self.subchannel is None:
                return True
            user = self.get_user(env)
            guest = self.get_guest(env)
            return self.subchannel is None and (
                (user and user == env.user and not env.user._is_public())
                or (guest and guest == env["mail.guest"]._get_guest_from_context())
            )