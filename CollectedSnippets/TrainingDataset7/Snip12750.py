def render_js(self):
        return [
            (
                path.__html__()
                if hasattr(path, "__html__")
                else format_html('<script src="{}"></script>', self.absolute_path(path))
            )
            for path in self._js
        ]