def how_to_configure(self):
        return self._create_shell_configuration(
            content=u'eval `thefuck --alias`',
            path='~/.tcshrc',
            reload='tcsh')