def handle(self, **options):
        locale = options["locale"]
        exclude = options["exclude"]
        ignore_patterns = set(options["ignore_patterns"])
        self.verbosity = options["verbosity"]
        if options["fuzzy"]:
            self.program_options = [*self.program_options, "-f"]

        if find_command(self.program) is None:
            raise CommandError(
                f"Can't find {self.program}. Make sure you have GNU gettext "
                "tools 0.19 or newer installed."
            )

        basedirs = [os.path.join("conf", "locale"), "locale"]
        if os.environ.get("DJANGO_SETTINGS_MODULE"):
            from django.conf import settings

            basedirs.extend(settings.LOCALE_PATHS)

        # Walk entire tree, looking for locale directories
        for dirpath, dirnames, filenames in os.walk(".", topdown=True):
            # As we may modify dirnames, iterate through a copy of it instead
            for dirname in list(dirnames):
                if is_ignored_path(
                    os.path.normpath(os.path.join(dirpath, dirname)), ignore_patterns
                ):
                    dirnames.remove(dirname)
                elif dirname == "locale":
                    basedirs.append(os.path.join(dirpath, dirname))

        # Gather existing directories.
        basedirs = set(map(os.path.abspath, filter(os.path.isdir, basedirs)))

        if not basedirs:
            raise CommandError(
                "This script should be run from the Django Git "
                "checkout or your project or app tree, or with "
                "the settings module specified."
            )

        # Build locale list
        all_locales = []
        for basedir in basedirs:
            locale_dirs = filter(os.path.isdir, glob.glob("%s/*" % basedir))
            all_locales.extend(map(os.path.basename, locale_dirs))

        # Account for excluded locales
        locales = locale or all_locales
        locales = set(locales).difference(exclude)

        self.has_errors = False
        for basedir in basedirs:
            if locales:
                dirs = [
                    os.path.join(basedir, locale, "LC_MESSAGES") for locale in locales
                ]
            else:
                dirs = [basedir]
            locations = []
            for ldir in dirs:
                for dirpath, dirnames, filenames in os.walk(ldir):
                    locations.extend(
                        (dirpath, f) for f in filenames if f.endswith(".po")
                    )
            if locations:
                self.compile_messages(locations)

        if self.has_errors:
            raise CommandError("compilemessages generated one or more errors.")