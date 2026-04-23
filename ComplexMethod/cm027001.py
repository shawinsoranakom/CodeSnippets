def validate_multicast_nodes(val: dict[str, Any]) -> dict[str, Any]:
            """Validate the input nodes for multicast."""
            nodes: set[ZwaveNode] = val[const.ATTR_NODES]
            broadcast: bool = val[const.ATTR_BROADCAST]

            if not broadcast:
                has_at_least_one_node(val)

            # User must specify a node if they are attempting a broadcast and have more
            # than one zwave-js network.
            if (
                broadcast
                and not nodes
                and len(self._hass.config_entries.async_entries(const.DOMAIN)) > 1
            ):
                raise vol.Invalid(
                    "You must include at least one entity or device in the service call"
                )

            first_node = next((node for node in nodes), None)

            if first_node and not all(node.client.driver is not None for node in nodes):
                raise vol.Invalid(f"Driver not ready for all nodes: {nodes}")

            # If any nodes don't have matching home IDs, we can't run the command
            # because we can't multicast across multiple networks
            if (
                first_node
                and first_node.client.driver  # We checked the driver was ready above.
                and any(
                    node.client.driver.controller.home_id
                    != first_node.client.driver.controller.home_id
                    for node in nodes
                    if node.client.driver is not None
                )
            ):
                raise vol.Invalid(
                    "Multicast commands only work on devices in the same network"
                )

            return val