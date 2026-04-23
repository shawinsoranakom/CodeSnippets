def _pkg_status(self, info, filepath):
        if not os.path.exists(filepath):
            return self.NOT_INSTALLED

        # Check if the file has the correct size.
        try:
            filestat = os.stat(filepath)
        except OSError:
            return self.NOT_INSTALLED
        if filestat.st_size != int(info.size):
            return self.STALE

        # Check if the file's checksum matches
        if md5_hexdigest(filepath) != info.checksum:
            return self.STALE

        # If it's a zipfile, and it's been at least partially
        # unzipped, then check if it's been fully unzipped.
        if filepath.endswith(".zip"):
            unzipdir = filepath[:-4]
            if not os.path.exists(unzipdir):
                return self.INSTALLED  # but not unzipped -- ok!
            if not os.path.isdir(unzipdir):
                return self.STALE

            unzipped_size = sum(
                os.stat(os.path.join(d, f)).st_size
                for d, _, files in os.walk(unzipdir)
                for f in files
            )
            if unzipped_size != info.unzipped_size:
                return self.STALE

        # Otherwise, everything looks good.
        return self.INSTALLED