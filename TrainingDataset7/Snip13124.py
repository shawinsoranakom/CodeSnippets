def template_dirs(self):
        """
        Return a list of directories to search for templates.
        """
        # Immutable return value because it's cached and shared by callers.
        template_dirs = tuple(self.dirs)
        if self.app_dirs:
            template_dirs += get_app_template_dirs(self.app_dirname)
        return template_dirs