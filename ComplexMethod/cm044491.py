def set_defaults(self, helptext: str = "") -> None:
        """ Override for plugin specific config defaults.

        This method should always be overridden to add the help text for the global plugin group.
        If `helptext` is not provided, then it is assumed that there is no global section for this
        plugin group.

        The default action will parse the child class' module for
        :class:`~lib.config.objects.ConfigItem` objects and add them to this plugin group's
        "global" section of :attr:`sections`.

        The name of each config option will be the variable name found in the module.

        It will then parse the child class' module for subclasses of
        :class:`~lib.config.objects.GlobalSection` objects and add each of these sections to this
        plugin group's :attr:`sections`, adding any :class:`~lib.config.objects.ConfigItem` within
        the GlobalSection to that sub-section.

        The section name will be the name of the GlobalSection subclass, lowercased

        Parameters
        ----------
        helptext : str
            The help text to display for the plugin group

        Raises
        ------
        ValueError
            If the plugin group's help text has not been provided
        """
        section = "global"
        logger.debug("[%s:%s] Adding defaults", self._plugin_group, section)

        if not helptext:
            logger.debug("No help text provided for '%s'. Not creating global section",
                         self.__module__)
            return

        self.add_section(section, helptext)

        for key, val in vars(sys.modules[self.__module__]).items():
            if isinstance(val, ConfigItem):
                self.add_item(section=section, title=key, config_item=val)
        logger.debug("[%s:%s] Added defaults", self._plugin_group, section)

        # Add global sub-sections
        for key, val in vars(sys.modules[self.__module__]).items():
            if inspect.isclass(val) and issubclass(val, GlobalSection) and val != GlobalSection:
                g_val = T.cast(GlobalSection, val)
                section_name = f"{section}.{key.lower()}"
                self.add_section(section_name, g_val.helptext)
                for opt_name, opt in g_val.__dict__.items():
                    if isinstance(opt, ConfigItem):
                        self.add_item(section=section_name, title=opt_name, config_item=opt)