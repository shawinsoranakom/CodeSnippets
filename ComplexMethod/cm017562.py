def delete_file(self, path, prefixed_path, source_storage):
        """
        Check if the target file should be deleted if it already exists.
        """
        if self.storage.exists(prefixed_path):
            try:
                # When was the target file modified last time?
                target_last_modified = self.storage.get_modified_time(prefixed_path)
            except (OSError, NotImplementedError):
                # The storage doesn't support get_modified_time() or failed
                pass
            else:
                try:
                    # When was the source file modified last time?
                    source_last_modified = source_storage.get_modified_time(path)
                except (OSError, NotImplementedError):
                    pass
                else:
                    # The full path of the target file
                    if self.local:
                        full_path = self.storage.path(prefixed_path)
                        # If it's --link mode and the path isn't a link (i.e.
                        # the previous collectstatic wasn't with --link) or if
                        # it's non-link mode and the path is a link (i.e. the
                        # previous collectstatic was with --link), the old
                        # links/files must be deleted so it's not safe to skip
                        # unmodified files.
                        can_skip_unmodified_files = not (
                            self.symlink ^ os.path.islink(full_path)
                        )
                    else:
                        # In remote storages, skipping is only based on the
                        # modified times since symlinks aren't relevant.
                        can_skip_unmodified_files = True
                    # Avoid sub-second precision (see #14665, #19540)
                    file_is_unmodified = target_last_modified.replace(
                        microsecond=0
                    ) >= source_last_modified.replace(microsecond=0)
                    if file_is_unmodified and can_skip_unmodified_files:
                        if prefixed_path not in self.unmodified_files:
                            self.unmodified_files.append(prefixed_path)
                        self.log("Skipping '%s' (not modified)" % path)
                        return False
            # Then delete the existing file if really needed
            if self.dry_run:
                self.log("Pretending to delete '%s'" % path)
            else:
                self.log("Deleting '%s'" % path)
                self.storage.delete(prefixed_path)
        return True