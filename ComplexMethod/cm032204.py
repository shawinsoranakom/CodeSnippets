def _download_package(self, info, download_dir, force):
        yield StartPackageMessage(info)
        yield ProgressMessage(0)

        # Do we already have the current version?
        status = self.status(info, download_dir)
        if not force and status == self.INSTALLED:
            yield UpToDateMessage(info)
            yield ProgressMessage(100)
            yield FinishPackageMessage(info)
            return

        # Remove the package from our status cache
        self._status_cache.pop(info.id, None)

        # Check for (and remove) any old/stale version.
        filepath = os.path.join(download_dir, info.filename)
        if os.path.exists(filepath):
            if status == self.STALE:
                yield StaleMessage(info)
            os.remove(filepath)

        # Ensure the download_dir exists
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        if not os.path.exists(os.path.join(download_dir, info.subdir)):
            os.makedirs(os.path.join(download_dir, info.subdir))

        # Download the file.  This will raise an IOError if the url
        # is not found.
        yield StartDownloadMessage(info)
        yield ProgressMessage(5)
        try:
            # logger.info('+++====' + info.url)
            infile = urlopen(info.url)
            with open(filepath, "wb") as outfile:
                num_blocks = max(1, info.size / (1024 * 16))
                for block in itertools.count():
                    s = infile.read(1024 * 16)  # 16k blocks.
                    outfile.write(s)
                    if not s:
                        break
                    if block % 2 == 0:  # how often?
                        yield ProgressMessage(min(80, 5 + 75 * (block / num_blocks)))
            infile.close()
        except OSError as e:
            yield ErrorMessage(
                info,
                "Error downloading %r from <%s>:" "\n  %s" % (info.id, info.url, e),
            )
            return
        yield FinishDownloadMessage(info)
        yield ProgressMessage(80)

        # If it's a zipfile, uncompress it.
        if info.filename.endswith(".zip"):
            zipdir = os.path.join(download_dir, info.subdir)
            # Unzip if we're unzipping by default; *or* if it's already
            # been unzipped (presumably a previous version).
            if info.unzip or os.path.exists(os.path.join(zipdir, info.id)):
                yield StartUnzipMessage(info)
                for msg in _unzip_iter(filepath, zipdir, verbose=False):
                    # Somewhat of a hack, but we need a proper package reference
                    msg.package = info
                    yield msg
                yield FinishUnzipMessage(info)

        yield FinishPackageMessage(info)