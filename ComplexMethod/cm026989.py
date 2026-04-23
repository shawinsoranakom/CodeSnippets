async def websocket_add_node(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
    entry: ZwaveJSConfigEntry,
    client: Client,
    driver: Driver,
) -> None:
    """Add a node to the Z-Wave network."""
    controller = driver.controller
    inclusion_strategy = InclusionStrategy(msg[INCLUSION_STRATEGY])
    force_security = msg.get(FORCE_SECURITY)
    provisioning = (
        msg.get(PLANNED_PROVISIONING_ENTRY)
        or msg.get(QR_PROVISIONING_INFORMATION)
        or msg.get(QR_CODE_STRING)
    )
    dsk = msg.get(DSK)

    @callback
    def async_cleanup() -> None:
        """Remove signal listeners."""
        for unsub in unsubs:
            unsub()

    @callback
    def forward_event(event: dict) -> None:
        connection.send_message(
            websocket_api.event_message(msg[ID], {"event": event["event"]})
        )

    @callback
    def forward_dsk(event: dict) -> None:
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": event["event"], "dsk": event["dsk"]}
            )
        )

    @callback
    def forward_node_added(
        node: Node, low_security: bool, low_security_reason: str | None
    ) -> None:
        interview_unsubs = [
            node.on("interview started", forward_event),
            node.on("interview completed", forward_event),
            node.on("interview stage completed", forward_stage),
            node.on("interview failed", forward_event),
        ]
        unsubs.extend(interview_unsubs)
        node_details = {
            "node_id": node.node_id,
            "status": node.status,
            "ready": node.ready,
            "low_security": low_security,
            "low_security_reason": low_security_reason,
        }
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": "node added", "node": node_details}
            )
        )

    @callback
    def forward_requested_grant(event: dict) -> None:
        connection.send_message(
            websocket_api.event_message(
                msg[ID],
                {
                    "event": event["event"],
                    "requested_grant": event["requested_grant"].to_dict(),
                },
            )
        )

    @callback
    def forward_stage(event: dict) -> None:
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": event["event"], "stage": event["stageName"]}
            )
        )

    @callback
    def node_found(event: dict) -> None:
        node = event["node"]
        node_details = {
            "node_id": node["nodeId"],
        }
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": "node found", "node": node_details}
            )
        )

    @callback
    def node_added(event: dict) -> None:
        forward_node_added(
            event["node"],
            event["result"].get("lowSecurity", False),
            event["result"].get("lowSecurityReason"),
        )

    @callback
    def device_registered(device: dr.DeviceEntry) -> None:
        device_details = {
            "name": device.name,
            "id": device.id,
            "manufacturer": device.manufacturer,
            "model": device.model,
        }
        connection.send_message(
            websocket_api.event_message(
                msg[ID], {"event": "device registered", "device": device_details}
            )
        )

    connection.subscriptions[msg["id"]] = async_cleanup
    unsubs: list[Callable[[], None]] = [
        controller.on("inclusion started", forward_event),
        controller.on("inclusion failed", forward_event),
        controller.on("inclusion stopped", forward_event),
        controller.on("validate dsk and enter pin", forward_dsk),
        controller.on("grant security classes", forward_requested_grant),
        controller.on("node found", node_found),
        controller.on("node added", node_added),
        async_dispatcher_connect(
            hass, EVENT_DEVICE_ADDED_TO_REGISTRY, device_registered
        ),
    ]
    msg[DATA_UNSUBSCRIBE] = unsubs

    if controller.inclusion_state in (InclusionState.INCLUDING, InclusionState.BUSY):
        connection.send_result(
            msg[ID],
            True,  # Inclusion is already in progress
        )
        # Check for nodes that have been added but not fully included
        for node in controller.nodes.values():
            if node.status != NodeStatus.DEAD and not node.ready:
                forward_node_added(
                    node,
                    not node.is_secure,
                    None,
                )
    else:
        try:
            result = await controller.async_begin_inclusion(
                INCLUSION_STRATEGY_NOT_SMART_START[inclusion_strategy.value],
                force_security=force_security,
                provisioning=provisioning,
                dsk=dsk,
            )
        except ValueError as err:
            connection.send_error(
                msg[ID],
                ERR_INVALID_FORMAT,
                err.args[0],
            )
            return

        connection.send_result(
            msg[ID],
            result,
        )