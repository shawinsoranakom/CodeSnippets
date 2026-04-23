def _gc_file_store_unsafe(self):
        # retrieve the file names from the checklist
        checklist = {}
        for dirpath, _, filenames in os.walk(self._full_path('checklist')):
            dirname = os.path.basename(dirpath)
            for filename in filenames:
                fname = "%s/%s" % (dirname, filename)
                checklist[fname] = os.path.join(dirpath, filename)

        # Clean up the checklist. The checklist is split in chunks and files are garbage-collected
        # for each chunk.
        removed = 0
        for names in split_every(self.env.cr.IN_MAX, checklist):
            # determine which files to keep among the checklist
            self.env.cr.execute("SELECT store_fname FROM ir_attachment WHERE store_fname IN %s", [names])
            whitelist = set(row[0] for row in self.env.cr.fetchall())

            # remove garbage files, and clean up checklist
            for fname in names:
                filepath = checklist[fname]
                if fname not in whitelist:
                    try:
                        os.unlink(self._full_path(fname))
                        _logger.debug("_file_gc unlinked %s", self._full_path(fname))
                        removed += 1
                    except OSError:
                        _logger.info("_file_gc could not unlink %s", self._full_path(fname), exc_info=True)
                with contextlib.suppress(OSError):
                    os.unlink(filepath)

        _logger.info("filestore gc %d checked, %d removed", len(checklist), removed)