def _update_config(self,
                       page_only: bool,
                       config: FaceswapConfig,
                       category: str,
                       current_section: str) -> bool:
        """Update the FaceswapConfig item from the currently selected options

        Parameters
        ----------
        page_only : bool
            ``True`` saves just the currently selected page's options, ``False`` saves all the
            plugins options within the currently selected config.
        config : :class:`~lib.config.FaceswapConfig`
            The original config that is to be addressed
        category : str
            The configuration category to update
        current_section : str
            The section of the configuration to update

        Returns
        -------
        bool
            ``True`` if the config has been updated. ``False`` if it is unchanged
        """
        retval = False
        for section_name, section in config.sections.items():
            if page_only and section_name != current_section:
                logger.debug("Skipping section '%s' for page_only save", section_name)
                continue
            key = category
            key += f"|{section_name.replace('.', '|')}" if section_name != "global" else ""
            gui_opts = T.cast(dict[str, ControlPanelOption],
                              self._config_cpanel_dict[key]["options"])
            for option_name, option in section.options.items():
                new_opt = gui_opts[option_name].get()
                if new_opt == option.value or (isinstance(option.value, list) and
                                               set(str(new_opt).split()) == set(option.value)):
                    logger.debug("Skipping unchanged option '%s'", option_name)
                    continue
                fmt_opt = str(new_opt).split() if isinstance(option.value, list) else new_opt
                logger.debug("Updating '%s' from %s to %s",
                             option_name, repr(option.value), repr(fmt_opt))
                option.set(new_opt)
                retval = True
        return retval