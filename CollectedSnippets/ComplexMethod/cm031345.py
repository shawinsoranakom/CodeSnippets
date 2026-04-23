def global_matches(self, text):
        names = rlcompleter.Completer.global_matches(self, text)
        prefix = commonprefix(names)
        if prefix and prefix != text:
            return [prefix]

        names.sort()
        values = []
        for name in names:
            clean_name = name.rstrip(': ')
            if keyword.iskeyword(clean_name) or keyword.issoftkeyword(clean_name):
                values.append(None)
            else:
                try:
                    values.append(eval(name, self.namespace))
                except Exception:
                    values.append(None)
        if self.use_colors and names:
            return self.colorize_matches(names, values)
        return names