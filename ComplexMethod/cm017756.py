def handle(self, app_or_project, name, target=None, **options):
        self.app_or_project = app_or_project
        self.a_or_an = "an" if app_or_project == "app" else "a"
        self.paths_to_remove = []
        self.verbosity = options["verbosity"]

        self.validate_name(name)

        # if some directory is given, make sure it's nicely expanded
        if target is None:
            top_dir = os.path.join(os.getcwd(), name)
            try:
                os.makedirs(top_dir)
            except FileExistsError:
                raise CommandError("'%s' already exists" % top_dir)
            except OSError as e:
                raise CommandError(e)
        else:
            top_dir = os.path.abspath(os.path.expanduser(target))
            if app_or_project == "app":
                self.validate_name(os.path.basename(top_dir), "directory")
            if not os.path.exists(top_dir):
                try:
                    os.makedirs(top_dir)
                except OSError as e:
                    raise CommandError(e)

        # Find formatters, which are external executables, before input
        # from the templates can sneak into the path.
        formatter_paths = find_formatters()

        extensions = tuple(handle_extensions(options["extensions"]))
        extra_files = []
        excluded_directories = [".git", "__pycache__"]
        for file in options["files"]:
            extra_files.extend(map(lambda x: x.strip(), file.split(",")))
        if exclude := options.get("exclude"):
            for directory in exclude:
                excluded_directories.append(directory.strip())
        if self.verbosity >= 2:
            self.stdout.write(
                "Rendering %s template files with extensions: %s"
                % (app_or_project, ", ".join(extensions))
            )
            self.stdout.write(
                "Rendering %s template files with filenames: %s"
                % (app_or_project, ", ".join(extra_files))
            )
        base_name = "%s_name" % app_or_project
        base_subdir = "%s_template" % app_or_project
        base_directory = "%s_directory" % app_or_project
        camel_case_name = "camel_case_%s_name" % app_or_project
        camel_case_value = "".join(x for x in name.title() if x != "_")

        context = Context(
            {
                **options,
                base_name: name,
                base_directory: top_dir,
                camel_case_name: camel_case_value,
                "docs_version": get_docs_version(),
                "django_version": django.__version__,
            },
            autoescape=False,
        )

        # Setup a stub settings environment for template rendering
        if not settings.configured:
            settings.configure()
            django.setup()

        template_dir = self.handle_template(options["template"], base_subdir)
        prefix_length = len(template_dir) + 1

        for root, dirs, files in os.walk(template_dir):
            path_rest = root[prefix_length:]
            relative_dir = path_rest.replace(base_name, name)
            if relative_dir:
                target_dir = os.path.join(top_dir, relative_dir)
                os.makedirs(target_dir, exist_ok=True)

            for dirname in dirs[:]:
                if "exclude" not in options:
                    if dirname.startswith(".") or dirname == "__pycache__":
                        dirs.remove(dirname)
                elif dirname in excluded_directories:
                    dirs.remove(dirname)

            for filename in files:
                if filename.endswith((".pyo", ".pyc", ".py.class")):
                    # Ignore some files as they cause various breakages.
                    continue
                old_path = os.path.join(root, filename)
                new_path = os.path.join(
                    top_dir, relative_dir, filename.replace(base_name, name)
                )
                for old_suffix, new_suffix in self.rewrite_template_suffixes:
                    if new_path.endswith(old_suffix):
                        new_path = new_path.removesuffix(old_suffix) + new_suffix
                        break  # Only rewrite once

                if os.path.exists(new_path):
                    raise CommandError(
                        "%s already exists. Overlaying %s %s into an existing "
                        "directory won't replace conflicting files."
                        % (
                            new_path,
                            self.a_or_an,
                            app_or_project,
                        )
                    )

                # Only render the Python files, as we don't want to
                # accidentally render Django templates files
                if new_path.endswith(extensions) or filename in extra_files:
                    with open(old_path, encoding="utf-8") as template_file:
                        content = template_file.read()
                    template = Engine().from_string(content)
                    content = template.render(context)
                    with open(new_path, "w", encoding="utf-8") as new_file:
                        new_file.write(content)
                else:
                    shutil.copyfile(old_path, new_path)

                if self.verbosity >= 2:
                    self.stdout.write("Creating %s" % new_path)
                try:
                    self.apply_umask(old_path, new_path)
                    self.make_writeable(new_path)
                except OSError:
                    self.stderr.write(
                        "Notice: Couldn't set permission bits on %s. You're "
                        "probably using an uncommon filesystem setup. No "
                        "problem." % new_path,
                        self.style.NOTICE,
                    )

        if self.paths_to_remove:
            if self.verbosity >= 2:
                self.stdout.write("Cleaning up temporary files.")
            for path_to_remove in self.paths_to_remove:
                if os.path.isfile(path_to_remove):
                    os.remove(path_to_remove)
                else:
                    shutil.rmtree(path_to_remove)

        run_formatters([top_dir], **formatter_paths, stderr=self.stderr)