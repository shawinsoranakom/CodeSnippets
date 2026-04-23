async def _async_update_data(self) -> dict[str, BringData]:
        """Fetch the latest data from bring."""

        try:
            self.lists = (await self.bring.load_lists()).lists
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
        except BringAuthException as e:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="setup_authentication_exception",
                translation_placeholders={CONF_EMAIL: self.bring.mail},
            ) from e

        if self.previous_lists - (
            current_lists := {lst.listUuid for lst in self.lists}
        ):
            self._purge_deleted_lists()
        new_lists = current_lists - self.previous_lists
        self.previous_lists = current_lists

        list_dict: dict[str, BringData] = {}
        for lst in self.lists:
            if (
                (ctx := set(self.async_contexts()))
                and lst.listUuid not in ctx
                and lst.listUuid not in new_lists
            ):
                continue
            try:
                items = await self.bring.get_list(lst.listUuid)
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
                list_dict[lst.listUuid] = BringData(lst, items)

        return list_dict