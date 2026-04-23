def build_from_config(self, config):
        if not config:
            return
        status = False
        if "input_shape" in config:
            # Case: all inputs are in the first arg (possibly nested).
            if utils.is_default(self.build):
                status = self._build_by_run_for_single_pos_arg(
                    config["input_shape"]
                )
            else:
                try:
                    self.build(config["input_shape"])
                    status = True
                except:
                    pass
            self._build_shapes_dict = config

        elif "shapes_dict" in config:
            # Case: inputs were recorded as multiple keyword arguments.
            if utils.is_default(self.build):
                status = self._build_by_run_for_kwargs(config["shapes_dict"])
            else:
                try:
                    self.build(**config["shapes_dict"])
                    status = True
                except:
                    pass
            self._build_shapes_dict = config["shapes_dict"]

        if not status:
            warnings.warn(
                f"Model '{self.name}' had a build config, but the model "
                "cannot be built automatically in "
                "`build_from_config(config)`. "
                "You should implement "
                "`def build_from_config(self, config)`, "
                "and you might also want to implement the method "
                " that generates the config at saving time, "
                "`def get_build_config(self)`. "
                "The method `build_from_config()` is meant to "
                "create the state of the model (i.e. its variables) "
                "upon deserialization.",
                stacklevel=2,
            )