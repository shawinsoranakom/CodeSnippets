def _write_info_json(self, label, ie_result, infofn, overwrite=None):
        """ Write infojson and returns True = written, 'exists' = Already exists, False = skip, None = error """
        if overwrite is None:
            overwrite = self.params.get('overwrites', True)
        if not self.params.get('writeinfojson'):
            return False
        elif not infofn:
            self.write_debug(f'Skipping writing {label} infojson')
            return False
        elif not self._ensure_dir_exists(infofn):
            return None
        elif not overwrite and os.path.exists(infofn):
            self.to_screen(f'[info] {label.title()} metadata is already present')
            return 'exists'

        self.to_screen(f'[info] Writing {label} metadata as JSON to: {infofn}')
        try:
            write_json_file(self.sanitize_info(ie_result, self.params.get('clean_infojson', True)), infofn)
            return True
        except OSError:
            self.report_error(f'Cannot write {label} metadata to JSON file {infofn}')
            return None