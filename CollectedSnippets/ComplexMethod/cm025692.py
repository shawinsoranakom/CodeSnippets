def _login(self) -> bool:
        """Login to the camera."""
        caminfo = self._caminfo
        if self._connect_addr:
            addrs = [self._connect_addr]
        else:
            addrs = [caminfo["host"], caminfo["internalHost"]]

        client_cls: type[uvc_camera.UVCCameraClient]
        if self._nvr.server_version >= (3, 2, 0):
            client_cls = uvc_camera.UVCCameraClientV320
        else:
            client_cls = uvc_camera.UVCCameraClient

        if caminfo["username"] is None:
            caminfo["username"] = "ubnt"

        assert isinstance(caminfo["username"], str)

        camera = None
        for addr in addrs:
            try:
                camera = client_cls(addr, caminfo["username"], self._password)
                camera.login()
                _LOGGER.debug("Logged into UVC camera %s via %s", self._attr_name, addr)
                self._connect_addr = addr
                break
            except OSError:
                pass
            except uvc_camera.CameraConnectError:
                pass
            except uvc_camera.CameraAuthError:
                pass
        if not self._connect_addr:
            _LOGGER.error("Unable to login to camera")
            return False

        self._camera = camera
        self._caminfo = caminfo
        return True