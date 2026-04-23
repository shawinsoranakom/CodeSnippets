def handle(self, *args, **options):
        locale = options["locale"]
        exclude = options["exclude"]
        self.domain = options["domain"]
        self.verbosity = options["verbosity"]
        process_all = options["all"]
        extensions = options["extensions"]
        self.symlinks = options["symlinks"]

        ignore_patterns = options["ignore_patterns"]
        if options["use_default_ignore_patterns"]:
            ignore_patterns += ["CVS", ".*", "*~", "*.pyc"]
        self.ignore_patterns = list(set(ignore_patterns))

        # Avoid messing with mutable class variables
        if options["no_wrap"]:
            self.msgmerge_options = self.msgmerge_options[:] + ["--no-wrap"]
            self.msguniq_options = self.msguniq_options[:] + ["--no-wrap"]
            self.msgattrib_options = self.msgattrib_options[:] + ["--no-wrap"]
            self.xgettext_options = self.xgettext_options[:] + ["--no-wrap"]
        if options["no_location"]:
            self.msgmerge_options = self.msgmerge_options[:] + ["--no-location"]
            self.msguniq_options = self.msguniq_options[:] + ["--no-location"]
            self.msgattrib_options = self.msgattrib_options[:] + ["--no-location"]
            self.xgettext_options = self.xgettext_options[:] + ["--no-location"]
        if options["add_location"]:
            arg_add_location = "--add-location=%s" % options["add_location"]
            self.msgmerge_options = self.msgmerge_options[:] + [arg_add_location]
            self.msguniq_options = self.msguniq_options[:] + [arg_add_location]
            self.msgattrib_options = self.msgattrib_options[:] + [arg_add_location]
            self.xgettext_options = self.xgettext_options[:] + [arg_add_location]

        self.no_obsolete = options["no_obsolete"]
        self.keep_pot = options["keep_pot"]

        if self.domain not in ("django", "djangojs"):
            raise CommandError(
                "currently makemessages only supports domains "
                "'django' and 'djangojs'"
            )
        if self.domain == "djangojs":
            exts = extensions or ["js"]
        else:
            exts = extensions or ["html", "txt", "py"]
        self.extensions = handle_extensions(exts)

        if (not locale and not exclude and not process_all) or self.domain is None:
            raise CommandError(
                "Type '%s help %s' for usage information."
                % (os.path.basename(sys.argv[0]), sys.argv[1])
            )

        if self.verbosity > 1:
            self.stdout.write(
                "examining files with the extensions: %s"
                % get_text_list(list(self.extensions), "and")
            )

        self.invoked_for_django = False
        self.locale_paths = []
        self.default_locale_path = None
        if os.path.isdir(os.path.join("conf", "locale")):
            self.locale_paths = [os.path.abspath(os.path.join("conf", "locale"))]
            self.default_locale_path = self.locale_paths[0]
            self.ignore_patterns.append("views/templates/i18n_catalog.js")
            self.invoked_for_django = True
        else:
            if self.settings_available:
                for path in settings.LOCALE_PATHS:
                    locale_path = os.path.abspath(path)
                    if locale_path not in self.locale_paths:
                        self.locale_paths.append(locale_path)
            # Allow to run makemessages inside an app dir
            if os.path.isdir("locale"):
                locale_path = os.path.abspath("locale")
                if locale_path not in self.locale_paths:
                    self.locale_paths.append(locale_path)
            if self.locale_paths:
                self.default_locale_path = self.locale_paths[0]
                os.makedirs(self.default_locale_path, exist_ok=True)

        # Build locale list
        looks_like_locale = re.compile(r"[a-z]{2}")
        locale_dirs = filter(
            os.path.isdir, glob.glob("%s/*" % self.default_locale_path)
        )
        all_locales = [
            lang_code
            for lang_code in map(os.path.basename, locale_dirs)
            if looks_like_locale.match(lang_code)
        ]

        # Account for excluded locales
        if process_all:
            locales = all_locales
        else:
            locales = locale or all_locales
            locales = set(locales).difference(exclude)

        if locales:
            check_programs("msguniq", "msgmerge", "msgattrib")

        check_programs("xgettext")

        try:
            potfiles = self.build_potfiles()

            # Build po files for each selected locale
            for locale in locales:
                if not is_valid_locale(locale):
                    # Try to guess what valid locale it could be
                    # Valid examples are: en_GB, shi_Latn_MA and
                    # nl_NL-x-informal

                    # Search for characters followed by a non character (i.e.
                    # separator)
                    match = re.match(
                        r"^(?P<language>[a-zA-Z]+)"
                        r"(?P<separator>[^a-zA-Z])"
                        r"(?P<territory>.+)$",
                        locale,
                    )
                    if match:
                        locale_parts = match.groupdict()
                        language = locale_parts["language"].lower()
                        territory = (
                            locale_parts["territory"][:2].upper()
                            + locale_parts["territory"][2:]
                        )
                        proposed_locale = f"{language}_{territory}"
                    else:
                        # It could be a language in uppercase
                        proposed_locale = locale.lower()

                    # Recheck if the proposed locale is valid
                    if is_valid_locale(proposed_locale):
                        self.stdout.write(
                            "invalid locale %s, did you mean %s?"
                            % (
                                locale,
                                proposed_locale,
                            ),
                        )
                    else:
                        self.stdout.write("invalid locale %s" % locale)

                    continue
                if self.verbosity > 0:
                    self.stdout.write("processing locale %s" % locale)
                for potfile in potfiles:
                    self.write_po_file(potfile, locale)
        finally:
            if not self.keep_pot:
                self.remove_potfiles()