async def _async_update_data(self) -> dict[str, dict[int, SynoCamera]]:
        """Fetch all camera data from api."""
        surveillance_station = self.api.surveillance_station
        if TYPE_CHECKING:
            assert surveillance_station is not None
        current_data: dict[int, SynoCamera] = {
            camera.id: camera for camera in surveillance_station.get_all_cameras()
        }

        try:
            await surveillance_station.update()
        except SynologyDSMAPIErrorException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        new_data: dict[int, SynoCamera] = {
            camera.id: camera for camera in surveillance_station.get_all_cameras()
        }

        for cam_id, cam_data_new in new_data.items():
            if (
                (cam_data_current := current_data.get(cam_id)) is not None
                and cam_data_current.live_view.rtsp != cam_data_new.live_view.rtsp
            ):
                async_dispatcher_send(
                    self.hass,
                    f"{SIGNAL_CAMERA_SOURCE_CHANGED}_{self.config_entry.entry_id}_{cam_id}",
                    cam_data_new.live_view.rtsp,
                )

        return {"cameras": new_data}