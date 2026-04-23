def remove_orphaned_files(
        self,
        session_id: str,
        widget_id: str,
        newest_file_id: int,
        active_file_ids: List[int],
    ) -> None:
        """Remove 'orphaned' files: files that have been uploaded and
        subsequently deleted, but haven't yet been removed from memory.

        Because FileUploader can live inside forms, file deletion is made a
        bit tricky: a file deletion should only happen after the form is
        submitted.

        FileUploader's widget value is an array of numbers that has two parts:
        - The first number is always 'this.state.newestServerFileId'.
        - The remaining 0 or more numbers are the file IDs of all the
          uploader's uploaded files.

        When the server receives the widget value, it deletes "orphaned"
        uploaded files. An orphaned file is any file associated with a given
        FileUploader whose file ID is not in the active_file_ids, and whose
        ID is <= `newestServerFileId`.

        This logic ensures that a FileUploader within a form doesn't have any
        of its "unsubmitted" uploads prematurely deleted when the script is
        re-run.

        Safe to call from any thread.
        """
        file_list_id = (session_id, widget_id)
        with self._files_lock:
            file_list = self._files_by_id.get(file_list_id)
            if file_list is None:
                return

            # Remove orphaned files from the list:
            # - `f.id in active_file_ids`:
            #   File is currently tracked by the widget. DON'T remove.
            # - `f.id > newest_file_id`:
            #   file was uploaded *after* the widget  was most recently
            #   updated. (It's probably in a form.) DON'T remove.
            # - `f.id < newest_file_id and f.id not in active_file_ids`:
            #   File is not currently tracked by the widget, and was uploaded
            #   *before* this most recent update. This means it's been deleted
            #   by the user on the frontend, and is now "orphaned". Remove!
            new_list = [
                f for f in file_list if f.id > newest_file_id or f.id in active_file_ids
            ]
            self._files_by_id[file_list_id] = new_list
            num_removed = len(file_list) - len(new_list)

        if num_removed > 0:
            LOGGER.debug("Removed %s orphaned files" % num_removed)