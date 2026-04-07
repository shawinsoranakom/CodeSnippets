def _set_times_for_all_po_files(self):
        """
        Set access and modification times to the Unix epoch time for all the
        .po files.
        """
        for locale in self.LOCALES:
            os.utime(self.PO_FILE % locale, (0, 0))