def preprocess(self):
        """
        Preprocess (if necessary) a translatable file before passing it to
        xgettext GNU gettext utility.
        """
        if not self.is_templatized:
            return

        with open(self.path, encoding="utf-8") as fp:
            src_data = fp.read()

        if self.domain == "django":
            content = templatize(src_data, origin=self.path[2:])

        with open(self.work_path, "w", encoding="utf-8") as fp:
            fp.write(content)