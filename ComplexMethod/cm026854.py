async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            await self.hass.async_add_executor_job(self._init_proxmox)
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
                translation_placeholders={"error": repr(err)},
            ) from err
        except SSLError as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="ssl_error",
                translation_placeholders={"error": repr(err)},
            ) from err
        except ConnectTimeout as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="timeout_connect",
                translation_placeholders={"error": repr(err)},
            ) from err
        except ProxmoxServerError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="api_error_details",
                translation_placeholders={"error": repr(err)},
            ) from err
        except ProxmoxPermissionsError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="permissions_error",
            ) from err
        except ProxmoxNodesNotFoundError as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="no_nodes_found",
            ) from err
        except requests.exceptions.ConnectionError as err:
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": repr(err)},
            ) from err