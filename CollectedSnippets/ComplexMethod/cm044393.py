def _get_global_options(self) -> dict[str, ConfigItem]:
        """ Obtain all of the current global user config options

        Returns
        -------
        dict[str, :class:`lib.config.objects.ConfigItem`]
            All of the current global user configuration options
        """
        objects = {key: val for key, val in vars(cfg).items()
                   if isinstance(val, ConfigItem)
                   or isclass(val) and issubclass(val, GlobalSection) and val != GlobalSection}

        retval: dict[str, ConfigItem] = {}
        for key, obj in objects.items():
            if isinstance(obj, ConfigItem):
                retval[key] = obj
                continue
            for name, opt in obj.__dict__.items():
                if isinstance(opt, ConfigItem):
                    retval[name] = opt
        logger.debug("Loaded global config options: %s", {k: v.value for k, v in retval.items()})
        return retval