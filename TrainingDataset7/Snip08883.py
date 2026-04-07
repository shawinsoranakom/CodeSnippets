def download(self, url):
        """
        Download the given URL and return the file name.
        """

        def cleanup_url(url):
            tmp = url.rstrip("/")
            filename = tmp.split("/")[-1]
            if url.endswith("/"):
                display_url = tmp + "/"
            else:
                display_url = url
            return filename, display_url

        prefix = "django_%s_template_" % self.app_or_project
        tempdir = tempfile.mkdtemp(prefix=prefix, suffix="_download")
        self.paths_to_remove.append(tempdir)
        filename, display_url = cleanup_url(url)

        if self.verbosity >= 2:
            self.stdout.write("Downloading %s" % display_url)

        the_path = os.path.join(tempdir, filename)
        opener = build_opener()
        opener.addheaders = [("User-Agent", f"Django/{django.__version__}")]
        try:
            with opener.open(url) as source, open(the_path, "wb") as target:
                headers = source.info()
                target.write(source.read())
        except OSError as e:
            raise CommandError(
                "couldn't download URL %s to %s: %s" % (url, filename, e)
            )

        used_name = the_path.split("/")[-1]

        # Trying to get better name from response headers
        content_disposition = headers["content-disposition"]
        if content_disposition:
            _, params = parse_header_parameters(content_disposition)
            guessed_filename = params.get("filename") or used_name
        else:
            guessed_filename = used_name

        # Falling back to content type guessing
        ext = self.splitext(guessed_filename)[1]
        content_type = headers["content-type"]
        if not ext and content_type:
            ext = mimetypes.guess_extension(content_type)
            if ext:
                guessed_filename += ext

        # Move the temporary file to a filename that has better
        # chances of being recognized by the archive utils
        if used_name != guessed_filename:
            guessed_path = os.path.join(tempdir, guessed_filename)
            shutil.move(the_path, guessed_path)
            return guessed_path

        # Giving up
        return the_path