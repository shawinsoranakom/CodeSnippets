def post_process(self, filename, ie_info):
        """Run all the postprocessors on the given file."""
        info = dict(ie_info)
        info['filepath'] = filename
        pps_chain = []
        if ie_info.get('__postprocessors') is not None:
            pps_chain.extend(ie_info['__postprocessors'])
        pps_chain.extend(self._pps)
        for pp in pps_chain:
            files_to_delete = []
            try:
                files_to_delete, info = pp.run(info)
            except PostProcessingError as e:
                self.report_error(e.msg)
            if files_to_delete and not self.params.get('keepvideo', False):
                for old_filename in files_to_delete:
                    self.to_screen('Deleting original file %s (pass -k to keep)' % old_filename)
                    try:
                        os.remove(encodeFilename(old_filename))
                    except (IOError, OSError):
                        self.report_warning('Unable to remove downloaded original file')