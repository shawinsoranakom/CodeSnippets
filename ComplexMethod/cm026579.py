async def _async_validate_and_create(self) -> ConfigFlowResult:
        """Validate the OAuth token and create the config entry."""
        assert self._oauth_data is not None
        access_token = self._oauth_data[CONF_TOKEN][CONF_ACCESS_TOKEN]
        tibber_connection = tibber.Tibber(
            access_token=access_token,
            websession=async_get_clientsession(self.hass),
        )

        try:
            await tibber_connection.update_info()
        except TimeoutError:
            return await self.async_step_connection_error()
        except tibber.InvalidLoginError:
            return self.async_abort(reason=ERR_TOKEN)
        except (
            aiohttp.ClientError,
            tibber.RetryableHttpExceptionError,
        ):
            return await self.async_step_connection_error()
        except tibber.FatalHttpExceptionError:
            return self.async_abort(reason=ERR_CLIENT)

        await self.async_set_unique_id(tibber_connection.user_id)

        title = tibber_connection.name or "Tibber"
        if self.source == SOURCE_REAUTH:
            reauth_entry = self._get_reauth_entry()
            self._abort_if_unique_id_mismatch(
                reason="wrong_account",
                description_placeholders={"title": reauth_entry.title},
            )
            return self.async_update_reload_and_abort(
                reauth_entry,
                data=self._oauth_data,
                title=title,
            )

        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data=self._oauth_data)