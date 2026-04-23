def _check_availability(self):
        """Check availability of the device."""
        # return if we already processed this entity
        if self._ignore_availability is not None:
            return
        # only do the availability check for entities connected to a device (with `on` feature)
        if self.device is None or not hasattr(self.resource, "on"):
            self._ignore_availability = False
            return
        # ignore availability if user added device to ignore list
        if self.device.id in self.bridge.config_entry.options.get(
            CONF_IGNORE_AVAILABILITY, []
        ):
            self._ignore_availability = True
            self.logger.info(
                "Device %s is configured to ignore availability status. ",
                self.name,
            )
            return
        # certified products (normally) report their state correctly
        # no need for workaround/reporting
        if self.device.product_data.certified:
            self._ignore_availability = False
            return
        # some (3th party) Hue lights report their connection status incorrectly
        # causing the zigbee availability to report as disconnected while in fact
        # it can be controlled. If the light is reported unavailable
        # by the zigbee connectivity but the state changes its considered as a
        # malfunctioning device and we report it.
        # While the user should actually fix this issue, we allow to
        # ignore the availability for this light/device from the config options.
        cur_state = self.resource.on.on
        if self._last_state is None:
            self._last_state = cur_state
            return
        if zigbee := self.bridge.api.devices.get_zigbee_connectivity(self.device.id):
            if (
                self._last_state != cur_state
                and zigbee.status != ConnectivityServiceStatus.CONNECTED
            ):
                # the device state changed from on->off or off->on
                # while it was reported as not connected!
                self.logger.warning(
                    (
                        "Device %s changed state while reported as disconnected. This"
                        " might be an indicator that routing is not working for this"
                        " device or the device is having connectivity issues. You can"
                        " disable availability reporting for this device in the Hue"
                        " options. Device details: %s - %s (%s) fw: %s"
                    ),
                    self.name,
                    self.device.product_data.manufacturer_name,
                    self.device.product_data.product_name,
                    self.device.product_data.model_id,
                    self.device.product_data.software_version,
                )
                # set attribute to false because we only want to log once per light/device.
                # a user must opt-in to ignore availability through integration options
                self._ignore_availability = False
        self._last_state = cur_state