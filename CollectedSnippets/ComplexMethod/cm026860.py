def _get_nodes_data(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the user input and fetch data (sync, for executor)."""
    auth_kwargs = {
        "password": data.get(CONF_PASSWORD),
    }
    if data.get(CONF_TOKEN):
        auth_kwargs = {
            "token_name": data[CONF_TOKEN_ID],
            "token_value": data[CONF_TOKEN_SECRET],
        }
    data = sanitize_config_entry(data)
    try:
        client = ProxmoxAPI(
            host=data[CONF_HOST],
            port=data[CONF_PORT],
            user=data[CONF_USERNAME],
            verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            **auth_kwargs,
        )
        nodes = client.nodes.get()
    except AuthenticationError as err:
        raise ProxmoxAuthenticationError from err
    except SSLError as err:
        raise ProxmoxSSLError from err
    except ConnectTimeout as err:
        raise ProxmoxConnectTimeout from err
    except ResourceException as err:
        raise ProxmoxNoNodesFound from err
    except requests.exceptions.ConnectionError as err:
        raise ProxmoxConnectionError from err

    nodes_data: list[dict[str, Any]] = []
    for node in nodes:
        try:
            vms = client.nodes(node["node"]).qemu.get()
            containers = client.nodes(node["node"]).lxc.get()
        except ResourceException as err:
            raise ProxmoxNoNodesFound from err
        except requests.exceptions.ConnectionError as err:
            raise ProxmoxConnectionError from err

        nodes_data.append(
            {
                CONF_NODE: node["node"],
                CONF_VMS: [vm["vmid"] for vm in vms],
                CONF_CONTAINERS: [container["vmid"] for container in containers],
            }
        )

    _LOGGER.debug("Nodes with data: %s", nodes_data)
    return nodes_data