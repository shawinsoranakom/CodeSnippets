async def _create_gateway_port_entities(
        device: OmadaListDevice,
    ) -> None:
        """Create entities for a gateway's ports."""
        entities: list[Entity] = []
        gateway_coordinator = controller.gateway_coordinator
        if gateway_coordinator:
            gateway = gateway_coordinator.data[device.mac]
            entities.extend(
                OmadaDevicePortSwitchEntity[
                    OmadaGatewayCoordinator, OmadaGateway, OmadaGatewayPortStatus
                ](gateway_coordinator, gateway, p, str(p.port_number), desc)
                for p in gateway.port_status
                for desc in GATEWAY_PORT_STATUS_SWITCHES
                if desc.exists_func(gateway, p)
            )
            entities.extend(
                OmadaDevicePortSwitchEntity[
                    OmadaGatewayCoordinator, OmadaGateway, OmadaGatewayPortConfig
                ](gateway_coordinator, gateway, p, str(p.port_number), desc)
                for p in gateway.port_configs
                for desc in GATEWAY_PORT_CONFIG_SWITCHES
                if desc.exists_func(gateway, p)
            )
        async_add_entities(entities)