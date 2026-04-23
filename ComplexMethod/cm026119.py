def zha_device_info(self) -> dict[str, Any]:
        """Get ZHA device information."""
        device_info: dict[str, Any] = {}
        device_info.update(self.device_info)
        device_info[ATTR_ACTIVE_COORDINATOR] = self.device.is_active_coordinator
        device_info[ENTITIES] = [
            {
                ATTR_ENTITY_ID: entity_ref.ha_entity_id,
                ATTR_NAME: entity_ref.ha_device_info[ATTR_NAME],
            }
            for entity_ref in self.gateway_proxy.ha_entity_refs[self.device.ieee]
        ]

        topology = self.gateway_proxy.gateway.application_controller.topology
        device_info[ATTR_NEIGHBORS] = [
            {
                ATTR_DEVICE_TYPE: neighbor.device_type.name,
                RX_ON_WHEN_IDLE: neighbor.rx_on_when_idle.name,
                RELATIONSHIP: neighbor.relationship.name,
                EXTENDED_PAN_ID: str(neighbor.extended_pan_id),
                ATTR_IEEE: str(neighbor.ieee),
                ATTR_NWK: str(neighbor.nwk),
                PERMIT_JOINING: neighbor.permit_joining.name,
                DEPTH: str(neighbor.depth),
                ATTR_LQI: str(neighbor.lqi),
            }
            for neighbor in topology.neighbors[self.device.ieee]
        ]

        device_info[ATTR_ROUTES] = [
            {
                DEST_NWK: str(route.DstNWK),
                ROUTE_STATUS: str(route.RouteStatus.name),
                MEMORY_CONSTRAINED: bool(route.MemoryConstrained),
                MANY_TO_ONE: bool(route.ManyToOne),
                ROUTE_RECORD_REQUIRED: bool(route.RouteRecordRequired),
                NEXT_HOP: str(route.NextHop),
            }
            for route in topology.routes[self.device.ieee]
        ]

        # Return endpoint device type Names
        names: list[dict[str, str]] = []
        for endpoint in (
            ep for epid, ep in self.device.device.endpoints.items() if epid
        ):
            profile = PROFILES.get(endpoint.profile_id)
            if profile and endpoint.device_type is not None:
                # DeviceType provides undefined enums
                names.append({ATTR_NAME: profile.DeviceType(endpoint.device_type).name})
            else:
                names.append(
                    {
                        ATTR_NAME: (
                            f"unknown {endpoint.device_type} device_type "
                            f"of 0x{(endpoint.profile_id or 0xFFFF):04x} profile id"
                        )
                    }
                )
        device_info[ATTR_ENDPOINT_NAMES] = names

        device_registry = dr.async_get(self.gateway_proxy.hass)
        reg_device = device_registry.async_get(self.device_id)
        if reg_device is not None:
            device_info[USER_GIVEN_NAME] = reg_device.name_by_user
            device_info[DEVICE_REG_ID] = reg_device.id
            device_info[ATTR_AREA_ID] = reg_device.area_id
        return device_info