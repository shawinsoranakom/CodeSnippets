def get_namespace(self, **options):
        if options and options.get("no_imports"):
            return {}

        verbosity = options["verbosity"] if options else 0

        try:
            apps.check_models_ready()
        except AppRegistryNotReady:
            if verbosity > 0:
                settings_env_var = os.getenv("DJANGO_SETTINGS_MODULE")
                self.stdout.write(
                    "Automatic imports are disabled since settings are not configured."
                    f"\nDJANGO_SETTINGS_MODULE value is {settings_env_var!r}.\n"
                    "HINT: Ensure that the settings module is configured and set.",
                    self.style.ERROR,
                    ending="\n\n",
                )
            return {}

        path_imports = self.get_auto_imports()
        if path_imports is None:
            return {}

        auto_imports = defaultdict(list)
        import_errors = []
        for path in path_imports:
            try:
                obj = import_dotted_path(path) if "." in path else import_module(path)
            except ImportError:
                import_errors.append(path)
                continue

            if "." in path:
                module, name = path.rsplit(".", 1)
            else:
                module = None
                name = path
            if (name, obj) not in auto_imports[module]:
                auto_imports[module].append((name, obj))

        namespace = {
            name: obj for items in auto_imports.values() for name, obj in items
        }

        if verbosity < 1:
            return namespace

        errors = len(import_errors)
        if errors:
            msg = "\n".join(f"  {e}" for e in import_errors)
            objects = "objects" if errors != 1 else "object"
            self.stdout.write(
                f"{errors} {objects} could not be automatically imported:\n\n{msg}",
                self.style.ERROR,
                ending="\n\n",
            )

        amount = len(namespace)
        objects_str = "objects" if amount != 1 else "object"
        msg = f"{amount} {objects_str} imported automatically"

        if verbosity < 2:
            if amount:
                msg += " (use -v 2 for details)"
            self.stdout.write(f"{msg}.", self.style.SUCCESS, ending="\n\n")
            return namespace

        top_level = auto_imports.pop(None, [])
        import_string = "\n".join(
            [f"  import {obj}" for obj, _ in top_level]
            + [
                f"  from {module} import {objects}"
                for module, imported_objects in auto_imports.items()
                if (objects := ", ".join(i[0] for i in imported_objects))
            ]
        )

        try:
            import isort
        except ImportError:
            pass
        else:
            import_string = isort.code(import_string)

        if import_string:
            msg = f"{msg}:\n\n{import_string}"
        else:
            msg = f"{msg}."

        self.stdout.write(msg, self.style.SUCCESS, ending="\n\n")

        return namespace