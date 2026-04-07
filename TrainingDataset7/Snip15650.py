def _ext_backend_paths(self):
        """
        Returns the paths for any external backend packages.
        """
        paths = []
        for backend in settings.DATABASES.values():
            package = backend["ENGINE"].split(".")[0]
            if package != "django":
                backend_pkg = __import__(package)
                backend_dir = os.path.dirname(backend_pkg.__file__)
                paths.append(os.path.dirname(backend_dir))
        return paths