def __init__(
        self,
        path,
        *,
        match=None,
        recursive=False,
        allow_files=True,
        allow_folders=False,
        **kwargs,
    ):
        self.path, self.match, self.recursive = path, match, recursive
        self.allow_files, self.allow_folders = allow_files, allow_folders
        super().__init__(choices=(), **kwargs)

        if self.required:
            self.choices = []
        else:
            self.choices = [("", get_blank_choice_label())]

        if self.match is not None:
            self.match_re = re.compile(self.match)

        if recursive:
            for root, dirs, files in sorted(os.walk(self.path)):
                if self.allow_files:
                    for f in sorted(files):
                        if self.match is None or self.match_re.search(f):
                            f = os.path.join(root, f)
                            self.choices.append((f, f.replace(path, "", 1)))
                if self.allow_folders:
                    for f in sorted(dirs):
                        if f == "__pycache__":
                            continue
                        if self.match is None or self.match_re.search(f):
                            f = os.path.join(root, f)
                            self.choices.append((f, f.replace(path, "", 1)))
        else:
            choices = []
            with os.scandir(self.path) as entries:
                for f in entries:
                    if f.name == "__pycache__":
                        continue
                    if (
                        (self.allow_files and f.is_file())
                        or (self.allow_folders and f.is_dir())
                    ) and (self.match is None or self.match_re.search(f.name)):
                        choices.append((f.path, f.name))
            choices.sort(key=operator.itemgetter(1))
            self.choices.extend(choices)

        self.widget.choices = self.choices