def GetExtensions(self, active_only=True,
                      editor_only=False, shell_only=False):
        """Return extensions in default and user config-extensions files.

        If active_only True, only return active (enabled) extensions
        and optionally only editor or shell extensions.
        If active_only False, return all extensions.
        """
        extns = self.RemoveKeyBindNames(
                self.GetSectionList('default', 'extensions'))
        userExtns = self.RemoveKeyBindNames(
                self.GetSectionList('user', 'extensions'))
        for extn in userExtns:
            if extn not in extns: #user has added own extension
                extns.append(extn)
        for extn in ('AutoComplete','CodeContext',
                     'FormatParagraph','ParenMatch'):
            extns.remove(extn)
            # specific exclusions because we are storing config for mainlined old
            # extensions in config-extensions.def for backward compatibility
        if active_only:
            activeExtns = []
            for extn in extns:
                if self.GetOption('extensions', extn, 'enable', default=True,
                                  type='bool'):
                    #the extension is enabled
                    if editor_only or shell_only:  # TODO both True contradict
                        if editor_only:
                            option = "enable_editor"
                        else:
                            option = "enable_shell"
                        if self.GetOption('extensions', extn,option,
                                          default=True, type='bool',
                                          warn_on_default=False):
                            activeExtns.append(extn)
                    else:
                        activeExtns.append(extn)
            return activeExtns
        else:
            return extns