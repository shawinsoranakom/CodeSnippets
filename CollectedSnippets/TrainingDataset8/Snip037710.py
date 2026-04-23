def handle_backmsg(self, msg: BackMsg) -> None:
        """Process a BackMsg."""
        try:
            msg_type = msg.WhichOneof("type")

            if msg_type == "rerun_script":
                if msg.debug_last_backmsg_id:
                    self._debug_last_backmsg_id = msg.debug_last_backmsg_id

                self._handle_rerun_script_request(msg.rerun_script)
            elif msg_type == "load_git_info":
                self._handle_git_information_request()
            elif msg_type == "clear_cache":
                self._handle_clear_cache_request()
            elif msg_type == "set_run_on_save":
                self._handle_set_run_on_save_request(msg.set_run_on_save)
            elif msg_type == "stop_script":
                self._handle_stop_script_request()
            else:
                LOGGER.warning('No handler for "%s"', msg_type)

        except Exception as ex:
            LOGGER.error(ex)
            self.handle_backmsg_exception(ex)