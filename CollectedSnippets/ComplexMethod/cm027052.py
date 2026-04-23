async def _async_update_data(self) -> dict[str, BringActivityData]:
        """Fetch activity data from bring."""
        self.lists = self.coordinator.lists

        list_dict: dict[str, BringActivityData] = {}
        for lst in self.lists:
            if (
                ctx := set(self.coordinator.async_contexts())
            ) and lst.listUuid not in ctx:
                continue
            try:
                activity = await self.coordinator.bring.get_activity(lst.listUuid)
                users = await self.coordinator.bring.get_list_users(lst.listUuid)
            except BringAuthException as e:
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="setup_authentication_exception",
                    translation_placeholders={CONF_EMAIL: self.coordinator.bring.mail},
                ) from e
            except BringRequestException as e:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="setup_request_exception",
                ) from e
            except BringParseException as e:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="setup_parse_exception",
                ) from e
            else:
                list_dict[lst.listUuid] = BringActivityData(activity, users)

        return list_dict