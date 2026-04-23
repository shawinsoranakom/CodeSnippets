async def get_hosts_list_if_supported(
    fbx_api: Freepybox,
) -> tuple[bool, list[dict[str, Any]]]:
    """Hosts list is not supported when freebox is configured in bridge mode."""
    supports_hosts: bool = True
    fbx_devices: list[dict[str, Any]] = []
    try:
        fbx_interfaces = await fbx_api.lan.get_interfaces() or []
        for interface in fbx_interfaces:
            fbx_devices.extend(
                await fbx_api.lan.get_hosts_list(interface["name"]) or []
            )
    except HttpRequestError as err:
        if (
            (matcher := re.search(r"Request failed \(APIResponse: (.+)\)", str(err)))
            and is_json(json_str := matcher.group(1))
            and (json_resp := json.loads(json_str)).get("error_code") == "nodev"
        ):
            # No need to retry, Host list not available
            supports_hosts = False
            _LOGGER.debug(
                "Host list is not available using bridge mode (%s)",
                json_resp.get("msg"),
            )

        else:
            raise

    return supports_hosts, fbx_devices