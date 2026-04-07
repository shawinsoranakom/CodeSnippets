def iter_template_filenames(self, template_name):
        """
        Iterate over candidate files for template_name.

        Ignore files that don't lie inside configured template dirs to avoid
        directory traversal attacks.
        """
        for template_dir in self.template_dirs:
            try:
                yield safe_join(template_dir, template_name)
            except SuspiciousFileOperation:
                # The joined path was located outside of this template_dir
                # (it might be inside another one, so this isn't fatal).
                pass