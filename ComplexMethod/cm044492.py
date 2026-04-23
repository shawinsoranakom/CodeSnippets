def _set_defaults(self) -> None:
        """Load the plugin's default values, set the object names and order the sections, global
        first then alphabetically."""
        self.set_defaults()
        for section_name, section in self.sections.items():
            for opt_name, opt in section.options.items():
                opt.set_name(f"{self._plugin_group}.{section_name}.{opt_name}")

        global_keys = sorted(s for s in self.sections if s.startswith("global"))
        remaining_keys = sorted(s for s in self.sections if not s.startswith("global"))
        ordered = {k: self.sections[k] for k in global_keys + remaining_keys}

        self.sections = ordered