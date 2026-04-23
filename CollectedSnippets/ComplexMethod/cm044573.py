def _check_inputs(self) -> None:
        """Validate provided arguments are valid

        Raises
        ------
        ValueError
            If provided arguments are not valid
        """
        if self.args.action in self._actions_have_dir_input and not self.input.is_type("dir"):
            raise ValueError("The chosen action requires a directory as its input, but you "
                             f"entered: {self.input.path}")
        if self.args.action in self._actions_have_vid_input and not self.input.is_type("vid"):
            raise ValueError("The chosen action requires a video as its input, but you entered: "
                             f"{self.input.path}")
        if self.args.action in self._actions_have_dir_output and not self.output.is_type("dir"):
            raise ValueError("The chosen action requires a directory as its output, but you "
                             f"entered: {self.output.path}")
        if self.args.action in self._actions_have_vid_output and not self.output.is_type("vid"):
            raise ValueError("The chosen action requires a video as its output, but you entered: "
                             f"{self.output.path}")

        # Check that ref_vid is a video when it needs to be
        if self.args.action in self._actions_req_ref_video:
            if self.ref_vid.is_type("none"):
                raise ValueError("The file chosen as the reference video is not a video, either "
                                 f"leave the field blank or type 'None': {self.ref_vid.path}")
        elif self.args.action in self._actions_can_use_ref_video:
            if self.ref_vid.is_type("none"):
                logger.warning("Warning: no reference video was supplied, even though "
                               "one may be used with the chosen action. If this is "
                               "intentional then ignore this warning.")