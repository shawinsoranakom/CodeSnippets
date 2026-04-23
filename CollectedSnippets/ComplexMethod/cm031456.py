def save_all(self):
        """Save configuration changes to the user config file.

        Clear self in preparation for additional changes.
        Return changed for testing.
        """
        idleConf.userCfg['main'].Save()

        changed = False
        for config_type in self:
            cfg_type_changed = False
            page = self[config_type]
            for section in page:
                if section == 'HelpFiles':  # Remove it for replacement.
                    idleConf.userCfg['main'].remove_section('HelpFiles')
                    cfg_type_changed = True
                for item, value in page[section].items():
                    if self.save_option(config_type, section, item, value):
                        cfg_type_changed = True
            if cfg_type_changed:
                idleConf.userCfg[config_type].Save()
                changed = True
        for config_type in ['keys', 'highlight']:
            # Save these even if unchanged!
            idleConf.userCfg[config_type].Save()
        self.clear()
        # ConfigDialog caller must add the following call
        # self.save_all_changed_extensions()  # Uses a different mechanism.
        return changed