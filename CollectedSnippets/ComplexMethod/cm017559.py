def collect(self):
        """
        Perform the bulk of the work of collectstatic.

        Split off from handle() to facilitate testing.
        """
        if self.symlink and not self.local:
            raise CommandError("Can't symlink to a remote destination.")

        if self.clear:
            self.clear_dir("")

        if self.symlink:
            handler = self.link_file
        else:
            handler = self.copy_file

        found_files = {}
        for finder in get_finders():
            for path, storage in finder.list(self.ignore_patterns):
                # Prefix the relative path if the source storage contains it
                if getattr(storage, "prefix", None):
                    prefixed_path = os.path.join(storage.prefix, path)
                else:
                    prefixed_path = path

                if prefixed_path not in found_files:
                    found_files[prefixed_path] = (storage, path)
                    handler(path, prefixed_path, storage)
                else:
                    self.skipped_files.append(prefixed_path)
                    self.log(
                        "Found another file with the destination path '%s'. It "
                        "will be ignored since only the first encountered file "
                        "is collected. If this is not what you want, make sure "
                        "every static file has a unique path." % prefixed_path,
                        level=2,
                    )

        # Storage backends may define a post_process() method.
        if self.post_process and hasattr(self.storage, "post_process"):
            processor = self.storage.post_process(found_files, dry_run=self.dry_run)
            for original_path, processed_path, processed in processor:
                if isinstance(processed, Exception):
                    self.stderr.write("Post-processing '%s' failed!" % original_path)
                    # Add a blank line before the traceback, otherwise it's
                    # too easy to miss the relevant part of the error message.
                    self.stderr.write()
                    # Re-raise exceptions as CommandError and display notes.
                    message = str(processed)
                    if hasattr(processed, "__notes__"):
                        message += "\n" + "\n".join(processed.__notes__)
                    raise CommandError(message) from processed
                if processed:
                    self.log(
                        "Post-processed '%s' as '%s'" % (original_path, processed_path),
                        level=2,
                    )
                    self.post_processed_files.append(original_path)
                else:
                    self.log("Skipped post-processing '%s'" % original_path)

        return {
            "modified": self.copied_files + self.symlinked_files,
            "unmodified": self.unmodified_files,
            "post_processed": self.post_processed_files,
            "skipped": self.skipped_files,
            "deleted": self.deleted_files,
        }