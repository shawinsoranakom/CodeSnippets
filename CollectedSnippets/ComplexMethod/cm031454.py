def current_colors_and_keys(self, section):
        """Return the currently active name for Theme or Keys section.

        idlelib.config-main.def ('default') includes these sections

        [Theme]
        default= 1
        name= IDLE Classic
        name2=

        [Keys]
        default= 1
        name=
        name2=

        Item 'name2', is used for built-in ('default') themes and keys
        added after 2015 Oct 1 and 2016 July 1.  This kludge is needed
        because setting 'name' to a builtin not defined in older IDLEs
        to display multiple error messages or quit.
        See https://bugs.python.org/issue25313.
        When default = True, 'name2' takes precedence over 'name',
        while older IDLEs will just use name.  When default = False,
        'name2' may still be set, but it is ignored.
        """
        cfgname = 'highlight' if section == 'Theme' else 'keys'
        default = self.GetOption('main', section, 'default',
                                 type='bool', default=True)
        name = ''
        if default:
            name = self.GetOption('main', section, 'name2', default='')
        if not name:
            name = self.GetOption('main', section, 'name', default='')
        if name:
            source = self.defaultCfg if default else self.userCfg
            if source[cfgname].has_section(name):
                return name
        return "IDLE Classic" if section == 'Theme' else self.default_keys()