def _on_files_updated(self, file_list, **kwargs):
        self.filemgr_events.append(file_list)