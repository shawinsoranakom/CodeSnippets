def get(self, path: str) -> None:
        parts = path.split("/")
        component_name = parts[0]
        component_root = self._registry.get_component_path(component_name)
        if component_root is None:
            self.write("not found")
            self.set_status(404)
            return

        # follow symlinks to get an accurate normalized path
        component_root = os.path.realpath(component_root)
        filename = "/".join(parts[1:])
        abspath = os.path.realpath(os.path.join(component_root, filename))

        # Do NOT expose anything outside of the component root.
        if os.path.commonprefix([component_root, abspath]) != component_root or (
            not os.path.normpath(abspath).startswith(
                component_root
            )  # this is a recommendation from CodeQL, probably a bit redundant
        ):
            self.write("forbidden")
            self.set_status(403)
            return
        try:
            with open(abspath, "rb") as file:
                contents = file.read()
        except (OSError) as e:
            _LOGGER.error(
                "ComponentRequestHandler: GET %s read error", abspath, exc_info=e
            )
            self.write("read error")
            self.set_status(404)
            return

        self.write(contents)
        self.set_header("Content-Type", self.get_content_type(abspath))

        self.set_extra_headers(path)