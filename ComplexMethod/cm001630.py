def __setattr__(self, key, value):
        if key in options_builtin_fields:
            return super(Options, self).__setattr__(key, value)

        if self.data is not None:
            if key in self.data or key in self.data_labels:

                # Check that settings aren't globally frozen
                assert not cmd_opts.freeze_settings, "changing settings is disabled"

                # Get the info related to the setting being changed
                info = self.data_labels.get(key, None)
                if info.do_not_save:
                    return

                # Restrict component arguments
                comp_args = info.component_args if info else None
                if isinstance(comp_args, dict) and comp_args.get('visible', True) is False:
                    raise RuntimeError(f"not possible to set '{key}' because it is restricted")

                # Check that this section isn't frozen
                if cmd_opts.freeze_settings_in_sections is not None:
                    frozen_sections = list(map(str.strip, cmd_opts.freeze_settings_in_sections.split(','))) # Trim whitespace from section names
                    section_key = info.section[0]
                    section_name = info.section[1]
                    assert section_key not in frozen_sections, f"not possible to set '{key}' because settings in section '{section_name}' ({section_key}) are frozen with --freeze-settings-in-sections"

                # Check that this section of the settings isn't frozen
                if cmd_opts.freeze_specific_settings is not None:
                    frozen_keys = list(map(str.strip, cmd_opts.freeze_specific_settings.split(','))) # Trim whitespace from setting keys
                    assert key not in frozen_keys, f"not possible to set '{key}' because this setting is frozen with --freeze-specific-settings"

                # Check shorthand option which disables editing options in "saving-paths"
                if cmd_opts.hide_ui_dir_config and key in self.restricted_opts:
                    raise RuntimeError(f"not possible to set '{key}' because it is restricted with --hide_ui_dir_config")

                self.data[key] = value
                return

        return super(Options, self).__setattr__(key, value)