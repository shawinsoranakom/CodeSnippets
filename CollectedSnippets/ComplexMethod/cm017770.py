def process_locale_dir(self, locale_dir, files):
        """
        Extract translatable literals from the specified files, creating or
        updating the POT file for a given locale directory.

        Use the xgettext GNU gettext utility.
        """
        build_files = []
        for translatable in files:
            if self.verbosity > 1:
                self.stdout.write(
                    "processing file %s in %s"
                    % (translatable.file, translatable.dirpath)
                )
            if self.domain not in ("djangojs", "django"):
                continue
            build_file = self.build_file_class(self, self.domain, translatable)
            try:
                build_file.preprocess()
            except UnicodeDecodeError as e:
                self.stdout.write(
                    "UnicodeDecodeError: skipped file %s in %s (reason: %s)"
                    % (
                        translatable.file,
                        translatable.dirpath,
                        e,
                    )
                )
                continue
            except BaseException:
                # Cleanup before exit.
                for build_file in build_files:
                    build_file.cleanup()
                raise
            build_files.append(build_file)

        if self.domain == "djangojs":
            args = [
                "xgettext",
                "-d",
                self.domain,
                "--language=JavaScript",
                "--keyword=gettext_noop",
                "--keyword=gettext_lazy",
                "--keyword=ngettext_lazy:1,2",
                "--keyword=pgettext:1c,2",
                "--keyword=npgettext:1c,2,3",
                "--output=-",
            ]
        elif self.domain == "django":
            args = [
                "xgettext",
                "-d",
                self.domain,
                "--language=Python",
                "--keyword=gettext_noop",
                "--keyword=gettext_lazy",
                "--keyword=ngettext_lazy:1,2",
                "--keyword=pgettext:1c,2",
                "--keyword=npgettext:1c,2,3",
                "--keyword=pgettext_lazy:1c,2",
                "--keyword=npgettext_lazy:1c,2,3",
                "--output=-",
            ]
        else:
            return

        input_files = [bf.work_path for bf in build_files]
        with NamedTemporaryFile(mode="w+") as input_files_list:
            input_files_list.write("\n".join(input_files))
            input_files_list.flush()
            args.extend(["--files-from", input_files_list.name])
            args.extend(self.xgettext_options)
            msgs, errors, status = popen_wrapper(args)

        if errors:
            if status != STATUS_OK:
                for build_file in build_files:
                    build_file.cleanup()
                raise CommandError(
                    "errors happened while running xgettext on %s\n%s"
                    % ("\n".join(input_files), errors)
                )
            elif self.verbosity > 0:
                # Print warnings
                self.stdout.write(errors)

        if msgs:
            if locale_dir is NO_LOCALE_DIR:
                for build_file in build_files:
                    build_file.cleanup()
                file_path = os.path.normpath(build_files[0].path)
                raise CommandError(
                    "Unable to find a locale path to store translations for "
                    "file %s. Make sure the 'locale' directory exists in an "
                    "app or LOCALE_PATHS setting is set." % file_path
                )
            for build_file in build_files:
                msgs = build_file.postprocess_messages(msgs)
            potfile = os.path.join(locale_dir, "%s.pot" % self.domain)
            write_pot_file(potfile, msgs)

        for build_file in build_files:
            build_file.cleanup()