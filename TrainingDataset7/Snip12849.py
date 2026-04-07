def _close_files(self):
        # Free up all file handles.
        # FIXME: this currently assumes that upload handlers store the file as
        # 'file'. We should document that...
        # (Maybe add handler.free_file to complement new_file)
        for handler in self._upload_handlers:
            if hasattr(handler, "file"):
                handler.file.close()