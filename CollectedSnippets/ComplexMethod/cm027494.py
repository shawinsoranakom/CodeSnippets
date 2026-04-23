async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        if not aiohomekit_const.BLE_TRANSPORT_SUPPORTED:
            return self.async_abort(reason="ignored_model")

        # Late imports in case BLE is not available
        from aiohomekit.controller.ble.discovery import BleDiscovery  # noqa: PLC0415
        from aiohomekit.controller.ble.manufacturer_data import (  # noqa: PLC0415
            HomeKitAdvertisement,
        )

        mfr_data = discovery_info.manufacturer_data

        try:
            device = HomeKitAdvertisement.from_manufacturer_data(
                discovery_info.name, discovery_info.address, mfr_data
            )
        except ValueError:
            return self.async_abort(reason="ignored_model")

        await self.async_set_unique_id(normalize_hkid(device.id))
        self._abort_if_unique_id_configured()

        if not (device.status_flags & StatusFlags.UNPAIRED):
            return self.async_abort(reason="already_paired")

        if self.controller is None:
            await self._async_setup_controller()
            assert self.controller is not None

        try:
            discovery = await self.controller.async_find(device.id)
        except aiohomekit.AccessoryNotFoundError:
            return self.async_abort(reason="accessory_not_found_error")

        if TYPE_CHECKING:
            discovery = cast(BleDiscovery, discovery)

        self.name = discovery.description.name
        self.model = BLE_DEFAULT_NAME
        self.category = discovery.description.category
        self.hkid = discovery.description.id

        return self._async_step_pair_show_form()