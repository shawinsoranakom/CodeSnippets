def _async_process_ws_message(self, message: WSSubscriptionMessage) -> None:
        """Process a message from the websocket."""
        if (new_obj := message.new_obj) is None:
            if isinstance(message.old_obj, ProtectAdoptableDeviceModel):
                self._async_remove_device(message.old_obj)
            return

        model_type = new_obj.model
        if model_type is ModelType.EVENT:
            if TYPE_CHECKING:
                assert isinstance(new_obj, Event)
            if _LOGGER.isEnabledFor(logging.DEBUG):
                log_event(new_obj)
            if (
                (new_obj.type is EventType.DEVICE_ADOPTED)
                and (metadata := new_obj.metadata)
                and (device_id := metadata.device_id)
                and (device := self.api.bootstrap.get_device_from_id(device_id))
            ):
                self._async_add_device(device)
            elif camera := new_obj.camera:
                self._async_signal_device_update(camera)
            elif light := new_obj.light:
                self._async_signal_device_update(light)
            elif sensor := new_obj.sensor:
                self._async_signal_device_update(sensor)
            return

        if model_type is ModelType.LIVEVIEW and len(self.api.bootstrap.viewers) > 0:
            # alert user viewport needs restart so voice clients can get new options
            _LOGGER.warning(
                "Liveviews updated. Restart Home Assistant to update Viewport select"
                " options"
            )
            return

        if message.old_obj is None and isinstance(new_obj, ProtectAdoptableDeviceModel):
            self._async_add_device(new_obj)
            return

        if getattr(new_obj, "is_adopted_by_us", True) and hasattr(new_obj, "mac"):
            if TYPE_CHECKING:
                assert isinstance(new_obj, (ProtectAdoptableDeviceModel, NVR))
            self._async_update_device(new_obj, message.changed_data)