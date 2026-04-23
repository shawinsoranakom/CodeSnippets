async def async_create_user(
        self,
        name: str | None,
        is_owner: bool | None = None,
        is_active: bool | None = None,
        system_generated: bool | None = None,
        credentials: models.Credentials | None = None,
        group_ids: list[str] | None = None,
        local_only: bool | None = None,
    ) -> models.User:
        """Create a new user."""
        groups = []
        for group_id in group_ids or []:
            if (group := self._groups.get(group_id)) is None:
                raise ValueError(f"Invalid group specified {group_id}")
            groups.append(group)

        kwargs: dict[str, Any] = {
            "name": name,
            # Until we get group management, we just put everyone in the
            # same group.
            "groups": groups,
            "perm_lookup": self._perm_lookup,
        }

        kwargs.update(
            {
                attr_name: value
                for attr_name, value in (
                    ("is_owner", is_owner),
                    ("is_active", is_active),
                    ("local_only", local_only),
                    ("system_generated", system_generated),
                )
                if value is not None
            }
        )

        new_user = models.User(**kwargs)

        while new_user.id in self._users:
            new_user = models.User(**kwargs)

        self._users[new_user.id] = new_user

        if credentials is None:
            self._async_schedule_save()
            return new_user

        # Saving is done inside the link.
        await self.async_link_user(new_user, credentials)
        return new_user