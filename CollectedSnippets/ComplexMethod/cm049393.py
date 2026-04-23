def print_raw(self, data, action_unique_id=None):
        job_id = False
        page_started = False
        try:
            with win32print_lock:
                job_id = win32print.StartDocPrinter(self.printer_handle, 1, ('', None, "RAW"))
                win32print.StartPagePrinter(self.printer_handle)
                page_started = True
                win32print.WritePrinter(self.printer_handle, data)
                win32print.EndPagePrinter(self.printer_handle)
                win32print.EndDocPrinter(self.printer_handle)
                self.job_ids.append(job_id)
                if action_unique_id:
                    self.job_action_ids[job_id] = action_unique_id
        except pywintypes.error as error:
            _logger.error("Error while printing raw data to printer %s: %s", self.device_name, error)
            if job_id or page_started:
                try:
                    with win32print_lock:
                        if page_started:
                            win32print.EndPagePrinter(self.printer_handle)
                        if job_id:
                            win32print.EndDocPrinter(self.printer_handle)
                            self.job_ids.append(job_id)
                            if action_unique_id:
                                self.job_action_ids[job_id] = action_unique_id
                except pywintypes.error as err:
                    _logger.error("Error while finalizing print job to printer %s after failure: %s", self.device_name, err)
                    self.send_status(status='error', message='ERROR_FAILED')
                    raise