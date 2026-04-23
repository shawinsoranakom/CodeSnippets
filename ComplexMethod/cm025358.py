def _update_callback(self) -> None:
        """Handle device update."""
        if self.block is not None or not self.coordinator.device.initialized:
            super()._update_callback()
            return

        _, entity_block, entity_sensor = self._attr_unique_id.split("-")

        assert self.coordinator.device.blocks

        for block in self.coordinator.device.blocks:
            if block.description != entity_block:
                continue

            for sensor_id in block.sensor_ids:
                if sensor_id != entity_sensor:
                    continue

                self.block = block
                LOGGER.debug("Entity %s attached to block", self.name)
                super()._update_callback()
                return