def get_tk_var(self, initial_value: str | bool | int | float) -> tk.Variable:
        """ Correct variable type for control

        Parameters
        ----------
        initial value : str | bool | int | float
            The initial value to set the tk.Variable to

        Returns
        -------
        :class:`tk.BooleanVar` | :class:`tk.IntVar` | :class:`tk.DoubleVar` | :class:`tk.StringVar`
            The correct tk.Variable for the given initial value
        """
        var: tk.Variable
        if self.dtype == bool:
            assert isinstance(initial_value, bool)
            var = tk.BooleanVar()
            var.set(initial_value)
        elif self.dtype == int:
            assert isinstance(initial_value, int)
            var = tk.IntVar()
            var.set(initial_value)
        elif self.dtype == float:
            assert isinstance(initial_value, float)
            var = tk.DoubleVar()
            var.set(initial_value)
        else:
            var = tk.StringVar()
            var.set(cast(str, initial_value))
        logger.debug("Setting tk variable: (name: '%s', dtype: %s, tk_var: %s, initial_value: %s)",
                     self.name, self.dtype, var, initial_value)
        if self._track_modified and self._command is not None:
            logger.debug("Tracking variable modification: %s", self.name)
            var.trace("w",
                      lambda name, index, mode, cmd=self._command: self._modified_callback(cmd))

        if self._track_modified and self._command == "train" and self.title == "Model Dir":
            var.trace("w", lambda name, index, mode, v=var: self._model_callback(v))

        return var