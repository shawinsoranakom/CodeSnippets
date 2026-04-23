def download(
        self,
        info_or_id=None,
        download_dir=None,
        quiet=False,
        force=False,
        prefix="[nltk_data] ",
        halt_on_error=True,
        raise_on_error=False,
        print_error_to=sys.stderr,
    ):

        print_to = functools.partial(print, file=print_error_to)
        # If no info or id is given, then use the interactive shell.
        if info_or_id is None:
            # [xx] hmm -- changing self._download_dir here seems like
            # the wrong thing to do.  Maybe the _interactive_download
            # function should make a new copy of self to use?
            if download_dir is not None:
                self._download_dir = download_dir
            self._interactive_download()
            return True

        else:
            # Define a helper function for displaying output:
            def show(s, prefix2=""):
                print_to(
                    textwrap.fill(
                        s,
                        initial_indent=prefix + prefix2,
                        subsequent_indent=prefix + prefix2 + " " * 4,
                    )
                )

            for msg in self.incr_download(info_or_id, download_dir, force):
                # Error messages
                if isinstance(msg, ErrorMessage):
                    show(msg.message)
                    if raise_on_error:
                        raise ValueError(msg.message)
                    if halt_on_error:
                        return False
                    self._errors = True
                    if not quiet:
                        print_to("Error installing package. Retry? [n/y/e]")
                        choice = input().strip()
                        if choice in ["y", "Y"]:
                            if not self.download(
                                msg.package.id,
                                download_dir,
                                quiet,
                                force,
                                prefix,
                                halt_on_error,
                                raise_on_error,
                            ):
                                return False
                        elif choice in ["e", "E"]:
                            return False

                # All other messages
                if not quiet:
                    # Collection downloading messages:
                    if isinstance(msg, StartCollectionMessage):
                        show("Downloading collection %r" % msg.collection.id)
                        prefix += "   | "
                        print_to(prefix)
                    elif isinstance(msg, FinishCollectionMessage):
                        print_to(prefix)
                        prefix = prefix[:-4]
                        if self._errors:
                            show(
                                "Downloaded collection %r with errors"
                                % msg.collection.id
                            )
                        else:
                            show("Done downloading collection %s" % msg.collection.id)

                    # Package downloading messages:
                    elif isinstance(msg, StartPackageMessage):
                        show(
                            "Downloading package %s to %s..."
                            % (msg.package.id, download_dir)
                        )
                    elif isinstance(msg, UpToDateMessage):
                        show("Package %s is already up-to-date!" % msg.package.id, "  ")
                    # elif isinstance(msg, StaleMessage):
                    #    show('Package %s is out-of-date or corrupt' %
                    #         msg.package.id, '  ')
                    elif isinstance(msg, StartUnzipMessage):
                        show("Unzipping %s." % msg.package.filename, "  ")

                    # Data directory message:
                    elif isinstance(msg, SelectDownloadDirMessage):
                        download_dir = msg.download_dir
        return True