def get_traceback_html(self):
        """Return HTML version of debug 500 HTTP error page."""
        with self.html_template_path.open(encoding="utf-8") as fh:
            t = DEBUG_ENGINE.from_string(fh.read())
        c = Context(self.get_traceback_data(), use_l10n=False)
        return t.render(c)