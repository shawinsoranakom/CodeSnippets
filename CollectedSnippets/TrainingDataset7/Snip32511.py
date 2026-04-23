def cached_file_path(self, path):
        fullpath = self.render_template(self.static_template_snippet(path))
        return fullpath.replace(settings.STATIC_URL, "")