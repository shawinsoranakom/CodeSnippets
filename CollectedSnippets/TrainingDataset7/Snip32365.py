def _get_file(self, filepath):
        assert filepath, "filepath is empty."
        filepath = os.path.join(settings.STATIC_ROOT, filepath)
        with open(filepath, encoding="utf-8") as f:
            return f.read()