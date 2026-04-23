async def _async_update_data(self):
        """Update data via API."""
        printer = None
        try:
            job = await self.octoprint.get_job_info()
        except UnauthorizedException as err:
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(err) from err

        # If octoprint is on, but the printer is disconnected
        # printer will return a 409, so continue using the last
        # reading if there is one
        try:
            printer = await self.octoprint.get_printer_info()
        except PrinterOffline:
            if not self._printer_offline:
                _LOGGER.debug("Unable to retrieve printer information: Printer offline")
                self._printer_offline = True
        except UnauthorizedException as err:
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(err) from err
        else:
            self._printer_offline = False

        return {"job": job, "printer": printer, "last_read_time": dt_util.utcnow()}