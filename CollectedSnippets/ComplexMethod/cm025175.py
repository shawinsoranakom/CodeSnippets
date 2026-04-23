async def async_load(self) -> None:
        """Load the users."""
        if self._loaded:
            raise RuntimeError("Auth storage is already loaded")
        self._loaded = True

        dev_reg = dr.async_get(self.hass)
        ent_reg = er.async_get(self.hass)
        data = await self._store.async_load()

        perm_lookup = PermissionLookup(ent_reg, dev_reg)
        self._perm_lookup = perm_lookup

        if data is None or not isinstance(data, dict):
            self._set_defaults()
            return

        users: dict[str, models.User] = {}
        groups: dict[str, models.Group] = {}
        credentials: dict[str, models.Credentials] = {}

        # Soft-migrating data as we load. We are going to make sure we have a
        # read only group and an admin group. There are two states that we can
        # migrate from:
        # 1. Data from a recent version which has a single group without policy
        # 2. Data from old version which has no groups
        has_admin_group = False
        has_user_group = False
        has_read_only_group = False
        group_without_policy = None

        # When creating objects we mention each attribute explicitly. This
        # prevents crashing if user rolls back HA version after a new property
        # was added.

        for group_dict in data.get("groups", []):
            policy: PolicyType | None = None

            if group_dict["id"] == GROUP_ID_ADMIN:
                has_admin_group = True

                name = GROUP_NAME_ADMIN
                policy = system_policies.ADMIN_POLICY
                system_generated = True

            elif group_dict["id"] == GROUP_ID_USER:
                has_user_group = True

                name = GROUP_NAME_USER
                policy = system_policies.USER_POLICY
                system_generated = True

            elif group_dict["id"] == GROUP_ID_READ_ONLY:
                has_read_only_group = True

                name = GROUP_NAME_READ_ONLY
                policy = system_policies.READ_ONLY_POLICY
                system_generated = True

            else:
                name = group_dict["name"]
                policy = group_dict.get("policy")
                system_generated = False

            # We don't want groups without a policy that are not system groups
            # This is part of migrating from state 1
            if policy is None:
                group_without_policy = group_dict["id"]
                continue

            groups[group_dict["id"]] = models.Group(
                id=group_dict["id"],
                name=name,
                policy=policy,
                system_generated=system_generated,
            )

        # If there are no groups, add all existing users to the admin group.
        # This is part of migrating from state 2
        migrate_users_to_admin_group = not groups and group_without_policy is None

        # If we find a no_policy_group, we need to migrate all users to the
        # admin group. We only do this if there are no other groups, as is
        # the expected state. If not expected state, not marking people admin.
        # This is part of migrating from state 1
        if groups and group_without_policy is not None:
            group_without_policy = None

        # This is part of migrating from state 1 and 2
        if not has_admin_group:
            admin_group = _system_admin_group()
            groups[admin_group.id] = admin_group

        # This is part of migrating from state 1 and 2
        if not has_read_only_group:
            read_only_group = _system_read_only_group()
            groups[read_only_group.id] = read_only_group

        if not has_user_group:
            user_group = _system_user_group()
            groups[user_group.id] = user_group

        for user_dict in data["users"]:
            # Collect the users group.
            user_groups = []
            for group_id in user_dict.get("group_ids", []):
                # This is part of migrating from state 1
                if group_id == group_without_policy:
                    group_id = GROUP_ID_ADMIN
                user_groups.append(groups[group_id])

            # This is part of migrating from state 2
            if not user_dict["system_generated"] and migrate_users_to_admin_group:
                user_groups.append(groups[GROUP_ID_ADMIN])

            users[user_dict["id"]] = models.User(
                name=user_dict["name"],
                groups=user_groups,
                id=user_dict["id"],
                is_owner=user_dict["is_owner"],
                is_active=user_dict["is_active"],
                system_generated=user_dict["system_generated"],
                perm_lookup=perm_lookup,
                # New in 2021.11
                local_only=user_dict.get("local_only", False),
            )

        for cred_dict in data["credentials"]:
            credential = models.Credentials(
                id=cred_dict["id"],
                is_new=False,
                auth_provider_type=cred_dict["auth_provider_type"],
                auth_provider_id=cred_dict["auth_provider_id"],
                data=cred_dict["data"],
            )
            credentials[cred_dict["id"]] = credential
            users[cred_dict["user_id"]].credentials.append(credential)

        for rt_dict in data["refresh_tokens"]:
            # Filter out the old keys that don't have jwt_key (pre-0.76)
            if "jwt_key" not in rt_dict:
                continue

            created_at = dt_util.parse_datetime(rt_dict["created_at"])
            if created_at is None:
                getLogger(__name__).error(
                    (
                        "Ignoring refresh token %(id)s with invalid created_at "
                        "%(created_at)s for user_id %(user_id)s"
                    ),
                    rt_dict,
                )
                continue

            if (token_type := rt_dict.get("token_type")) is None:
                if rt_dict["client_id"] is None:
                    token_type = models.TOKEN_TYPE_SYSTEM
                else:
                    token_type = models.TOKEN_TYPE_NORMAL

            # old refresh_token don't have last_used_at (pre-0.78)
            if last_used_at_str := rt_dict.get("last_used_at"):
                last_used_at = dt_util.parse_datetime(last_used_at_str)
            else:
                last_used_at = None

            token = models.RefreshToken(
                id=rt_dict["id"],
                user=users[rt_dict["user_id"]],
                client_id=rt_dict["client_id"],
                # use dict.get to keep backward compatibility
                client_name=rt_dict.get("client_name"),
                client_icon=rt_dict.get("client_icon"),
                token_type=token_type,
                created_at=created_at,
                access_token_expiration=timedelta(
                    seconds=rt_dict["access_token_expiration"]
                ),
                token=rt_dict["token"],
                jwt_key=rt_dict["jwt_key"],
                last_used_at=last_used_at,
                last_used_ip=rt_dict.get("last_used_ip"),
                expire_at=rt_dict.get("expire_at"),
                version=rt_dict.get("version"),
            )
            if "credential_id" in rt_dict:
                token.credential = credentials.get(rt_dict["credential_id"])
            users[rt_dict["user_id"]].refresh_tokens[token.id] = token

        self._groups = groups
        self._users = users
        self._build_token_id_to_user_id()
        self._async_schedule_save(INITIAL_LOAD_SAVE_DELAY)