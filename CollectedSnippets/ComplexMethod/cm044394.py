def _update_config(self) -> None:
        """ Update the loaded training config with the one contained within the values loaded
        from the state file.

        Check for any `fixed`=``False`` parameter changes and log info changes.

        Update any legacy config items to their current versions.
        """
        legacy_update = self._update_legacy_config()
        # Add any new items to state config for legacy purposes where the new default may be
        # detrimental to an existing model.
        legacy_defaults: dict[str, str | int | bool | float] = {"centering": "legacy",
                                                                "coverage": 62.5,
                                                                "mask_loss_function": "mse",
                                                                "optimizer": "adam",
                                                                "mixed_precision": False}
        rebuild_tasks = ["mixed_precision"]
        options = self._get_global_options() | self._get_model_options()
        for key, opt in options.items():
            val: ConfigValueType = opt()

            if key not in self._config:
                val = legacy_defaults.get(key, val)
                logger.info("Adding new config item to state file: '%s': %s", key, repr(val))
                self._config[key] = val

            old_val = self._config[key]
            old_val = "none" if old_val is None else old_val  # We used to allow NoneType. No more

            if not opt.fixed:
                self._updateable_options.append(key)

            if not opt.fixed and val != old_val:
                self._config[key] = val
                logger.info("Config item: '%s' has been updated from %s to %s",
                            key, repr(old_val), repr(val))
                self._rebuild_model = self._rebuild_model or key in rebuild_tasks
                continue

            if val != old_val:
                logger.debug("Fixed config item '%s' Updated from %s to %s from state file",
                             key, repr(val), repr(old_val))
                opt.set(old_val)

        if legacy_update:
            self.save()
        logger.info("Using configuration saved in state file")
        logger.debug("Updateable items: %s", self._updateable_options)