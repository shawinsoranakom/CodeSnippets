async def async_login_flow(
        self, context: AuthFlowContext | None
    ) -> TrustedNetworksLoginFlow:
        """Return a flow to login."""
        assert context is not None
        ip_addr = cast(IPAddress, context.get("ip_address"))
        users = await self.store.async_get_users()
        available_users = [
            user for user in users if not user.system_generated and user.is_active
        ]
        for ip_net, user_or_group_list in self.trusted_users.items():
            if ip_addr not in ip_net:
                continue

            user_list = [
                user_id for user_id in user_or_group_list if isinstance(user_id, str)
            ]
            group_list = [
                group[CONF_GROUP]
                for group in user_or_group_list
                if isinstance(group, dict)
            ]
            flattened_group_list = [
                group for sublist in group_list for group in sublist
            ]
            available_users = [
                user
                for user in available_users
                if (
                    user.id in user_list
                    or any(group.id in flattened_group_list for group in user.groups)
                )
            ]
            break

        return TrustedNetworksLoginFlow(
            self,
            ip_addr,
            {user.id: user.name for user in available_users},
            self.config[CONF_ALLOW_BYPASS_LOGIN],
        )