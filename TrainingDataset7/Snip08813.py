def find_files(self, root):
        """
        Get all files in the given root. Also check that there is a matching
        locale dir for each file.
        """
        all_files = []
        ignored_roots = []
        if self.settings_available:
            ignored_roots = [
                os.path.normpath(p)
                for p in (settings.MEDIA_ROOT, settings.STATIC_ROOT)
                if p
            ]
        for dirpath, dirnames, filenames in os.walk(
            root, topdown=True, followlinks=self.symlinks
        ):
            for dirname in dirnames[:]:
                if (
                    is_ignored_path(
                        os.path.normpath(os.path.join(dirpath, dirname)),
                        self.ignore_patterns,
                    )
                    or os.path.join(os.path.abspath(dirpath), dirname) in ignored_roots
                ):
                    dirnames.remove(dirname)
                    if self.verbosity > 1:
                        self.stdout.write("ignoring directory %s" % dirname)
                elif dirname == "locale":
                    dirnames.remove(dirname)
                    locale_dir = os.path.join(os.path.abspath(dirpath), dirname)
                    if locale_dir in self.locale_paths:
                        self.locale_paths.remove(locale_dir)
                    self.locale_paths.insert(0, locale_dir)
            for filename in filenames:
                file_path = os.path.normpath(os.path.join(dirpath, filename))
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in self.extensions or is_ignored_path(
                    file_path, self.ignore_patterns
                ):
                    if self.verbosity > 1:
                        self.stdout.write(
                            "ignoring file %s in %s" % (filename, dirpath)
                        )
                else:
                    locale_dir = None
                    for path in self.locale_paths:
                        if os.path.abspath(dirpath).startswith(os.path.dirname(path)):
                            locale_dir = path
                            break
                    locale_dir = locale_dir or self.default_locale_path or NO_LOCALE_DIR
                    all_files.append(
                        self.translatable_file_class(dirpath, filename, locale_dir)
                    )
        return sorted(all_files)