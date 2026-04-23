def get_sequences(self):
        """Return a name-to-key-list dictionary to define each sequence."""
        results = {}
        try:
            f = open(os.path.join(self._path, '.mh_sequences'), 'r', encoding='ASCII')
        except FileNotFoundError:
            return results
        with f:
            all_keys = set(self.keys())
            for line in f:
                try:
                    name, contents = line.split(':')
                    keys = set()
                    for spec in contents.split():
                        if spec.isdigit():
                            keys.add(int(spec))
                        else:
                            start, stop = (int(x) for x in spec.split('-'))
                            keys.update(range(start, stop + 1))
                    results[name] = [key for key in sorted(keys) \
                                         if key in all_keys]
                    if len(results[name]) == 0:
                        del results[name]
                except ValueError:
                    raise FormatError('Invalid sequence specification: %s' %
                                      line.rstrip())
        return results