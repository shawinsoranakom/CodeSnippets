def how_to_configure(self):
        return self._create_shell_configuration(
            content=u"thefuck --alias | source",
            path='~/.config/fish/config.fish',
            reload='fish')