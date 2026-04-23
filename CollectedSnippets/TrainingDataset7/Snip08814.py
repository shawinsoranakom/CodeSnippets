def process_files(self, file_list):
        """
        Group translatable files by locale directory and run pot file build
        process for each group.
        """
        file_groups = {}
        for translatable in file_list:
            file_group = file_groups.setdefault(translatable.locale_dir, [])
            file_group.append(translatable)
        for locale_dir, files in file_groups.items():
            self.process_locale_dir(locale_dir, files)