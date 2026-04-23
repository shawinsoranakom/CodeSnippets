def update_logger(self, logger: logging.Logger | None = None) -> None:
        """Update logger."""
        self._set_logger(logger)
        for script in self._repeat_script.values():
            script.update_logger(self._logger)
        for parallel_scripts in self._parallel_scripts.values():
            for parallel_script in parallel_scripts:
                parallel_script.update_logger(self._logger)
        for choose_data in self._choose_data.values():
            for _, script in choose_data["choices"]:
                script.update_logger(self._logger)
            if choose_data["default"] is not None:
                choose_data["default"].update_logger(self._logger)
        for if_data in self._if_data.values():
            if_data["if_then"].update_logger(self._logger)
            if if_data["if_else"] is not None:
                if_data["if_else"].update_logger(self._logger)