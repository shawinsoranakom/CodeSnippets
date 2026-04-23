def _set_fps(self) -> None:
        """Set :attr:`arguments.fps` based on input arguments"""
        # If fps was left blank in gui, set it to default -1.0 value
        if self.args.fps == "":
            self.args.fps = str(-1.0)

        # Try to set fps automatically if needed and not supplied by user
        if self.args.action in self._actions_req_fps \
                and self.__convert_fps(self.args.fps) <= 0:
            if self.__check_have_fps(["r", "i"]):
                _error_str = "No fps, input or reference video was supplied, "
                _error_str += "hence it's not possible to "
                _error_str += f"'{self.args.action}'."
                raise ValueError(_error_str)
            if self.output.fps is not None and self.__check_have_fps(["r", "i"]):
                self.args.fps = self.output.fps
            elif self.ref_vid.fps is not None and self.__check_have_fps(["i"]):
                self.args.fps = self.ref_vid.fps
            elif self.input.fps is not None and self.__check_have_fps(["r"]):
                self.args.fps = self.input.fps