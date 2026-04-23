def _get_file(self, filepath):
        path = call_command(
            "findstatic", filepath, all=False, verbosity=0, stdout=StringIO()
        )
        with open(path, encoding="utf-8") as f:
            return f.read()