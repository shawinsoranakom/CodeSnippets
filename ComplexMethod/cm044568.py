def _output_results(self, items_output: list[str] | list[tuple[str, int]]) -> None:
        """Output the results in the requested format

        Parameters
        ----------
        items_output
            The list of frame names, and potentially face ids, of any items which met the
            selection criteria
        """
        logger.trace("items_output: %s", items_output)  # type:ignore
        if self._output == "move" and self._is_video and self._type == "frames":
            logger.warning("Move was selected with an input video. This is not possible so "
                           "falling back to console output")
            self._output = "console"
        if not items_output:
            logger.info("No %s were found meeting the criteria", self._type)
            return
        if self._output == "move":
            self._move_file(items_output)
            return
        if self._job == "multi-faces" and self._type == "faces":
            # Strip the index for printed/file output
            final_output = [item[0] for item in items_output]
        else:
            final_output = T.cast(list[str], items_output)
        output_message = "-----------------------------------------------\r\n"
        output_message += f" {self.output_message} ({len(final_output)})\r\n"
        output_message += "-----------------------------------------------\r\n"
        output_message += "\r\n".join(final_output)
        if self._output == "console":
            for line in output_message.splitlines():
                logger.info(line)
        if self._output == "file":
            self.output_file(output_message, len(final_output))