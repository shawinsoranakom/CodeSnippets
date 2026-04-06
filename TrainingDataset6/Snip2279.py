def how_to_configure(self):
        return ShellConfiguration(
            content=u'iex "$(thefuck --alias)"',
            path='$profile',
            reload='. $profile',
            can_configure_automatically=False)