def hasprompt(self, *args):
        lower = self.prompt.lower()
        if self.p is None or self.prompt is None:
            return None
        outres = ""
        for arg in args:
            if arg != "":
                division = arg.split("|")
                expected = division[0].lower()
                default = division[1] if len(division) > 1 else ""
                if lower.find(expected) >= 0:
                    outres = f'{outres}{expected}'
                else:
                    outres = outres if default == "" else f'{outres}{default}'
        return sanitize_filename_part(outres)