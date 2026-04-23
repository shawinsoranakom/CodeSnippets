def ApplyKeybindings(self):
        """Apply the virtual, configurable keybindings.

        Also update hotkeys to current keyset.
        """
        # Called from configdialog.activate_config_changes.
        self.mainmenu.default_keydefs = keydefs = idleConf.GetCurrentKeySet()
        self.apply_bindings()
        for extensionName in self.get_standard_extension_names():
            xkeydefs = idleConf.GetExtensionBindings(extensionName)
            if xkeydefs:
                self.apply_bindings(xkeydefs)

        # Update menu accelerators.
        menuEventDict = {}
        for menu in self.mainmenu.menudefs:
            menuEventDict[menu[0]] = {}
            for item in menu[1]:
                if item:
                    menuEventDict[menu[0]][prepstr(item[0])[1]] = item[1]
        for menubarItem in self.menudict:
            menu = self.menudict[menubarItem]
            end = menu.index(END)
            if end is None:
                # Skip empty menus
                continue
            end += 1
            for index in range(0, end):
                if menu.type(index) == 'command':
                    accel = menu.entrycget(index, 'accelerator')
                    if accel:
                        itemName = menu.entrycget(index, 'label')
                        event = ''
                        if menubarItem in menuEventDict:
                            if itemName in menuEventDict[menubarItem]:
                                event = menuEventDict[menubarItem][itemName]
                        if event:
                            accel = get_accelerator(keydefs, event)
                            menu.entryconfig(index, accelerator=accel)