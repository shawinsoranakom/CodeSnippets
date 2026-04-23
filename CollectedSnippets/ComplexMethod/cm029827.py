def set_sequences(self, sequences):
        """Set sequences using the given name-to-key-list dictionary."""
        f = self._open_mh_sequences_file(text=True)
        try:
            os.close(os.open(f.name, os.O_WRONLY | os.O_TRUNC))
            for name, keys in sequences.items():
                if len(keys) == 0:
                    continue
                f.write(name + ':')
                prev = None
                completing = False
                for key in sorted(set(keys)):
                    if key - 1 == prev:
                        if not completing:
                            completing = True
                            f.write('-')
                    elif completing:
                        completing = False
                        f.write('%s %s' % (prev, key))
                    else:
                        f.write(' %s' % key)
                    prev = key
                if completing:
                    f.write(str(prev) + '\n')
                else:
                    f.write('\n')
        finally:
            _sync_close(f)