def _set_loss_names(self, outputs: list[KerasTensor]) -> None:
        """Name the losses based on model output.

        This is used for correct naming in the state file, for display purposes only.

        Adds the loss names to :attr:`names`

        Parameters
        ----------
        A list of output tensors from the model plugin
        """
        # TODO Use output names if/when these are fixed upstream
        split_outputs = [outputs[:len(outputs) // 2], outputs[len(outputs) // 2:]]
        for side, side_output in zip(("a", "b"), split_outputs):
            output_names = [output.name for output in side_output]
            output_shapes = [output.shape[1:] for output in side_output]
            output_types = ["mask" if shape[-1] == 1 else "face" for shape in output_shapes]
            logger.debug("side: %s, output names: %s, output_shapes: %s, output_types: %s",
                         side, output_names, output_shapes, output_types)
            for idx, name in enumerate(output_types):
                suffix = "" if output_types.count(name) == 1 else f"_{idx}"
                self._names.append(f"{name}_{side}{suffix}")
        logger.debug(self._names)