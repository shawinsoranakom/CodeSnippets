async def _async_update_data(self) -> dict[str, ProxmoxNodeData]:
        """Fetch data from Proxmox VE API."""

        try:
            node_pairs = await self.hass.async_add_executor_job(self._fetch_all_nodes)
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
                translation_placeholders={"error": repr(err)},
            ) from err
        except SSLError as err:
            raise UpdateFailed(
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
        except ResourceException as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_nodes_found",
            ) from err
        except requests.exceptions.ConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": repr(err)},
            ) from err

        data: dict[str, ProxmoxNodeData] = {}
        for node, resources in node_pairs:
            data[node[CONF_NODE]] = ProxmoxNodeData(
                node=node,
                vms={int(vm["vmid"]): vm for vm in resources.vms},
                containers={
                    int(container["vmid"]): container
                    for container in resources.containers
                },
                storages={s["storage"]: s for s in resources.storages},
                backups=resources.backups,
            )

        self._async_add_remove_nodes(data)
        return data