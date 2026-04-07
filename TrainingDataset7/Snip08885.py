def extract(self, filename):
        """
        Extract the given file to a temporary directory and return
        the path of the directory with the extracted content.
        """
        prefix = "django_%s_template_" % self.app_or_project
        tempdir = tempfile.mkdtemp(prefix=prefix, suffix="_extract")
        self.paths_to_remove.append(tempdir)
        if self.verbosity >= 2:
            self.stdout.write("Extracting %s" % filename)
        try:
            archive.extract(filename, tempdir)
            return tempdir
        except (archive.ArchiveException, OSError) as e:
            raise CommandError(
                "couldn't extract file %s to %s: %s" % (filename, tempdir, e)
            )