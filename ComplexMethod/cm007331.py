def __getattr__(self, name):
            self.__instantiate()
            if name == 'pattern':
                self.pattern = self.source
                return self.pattern
            elif hasattr(self.__self, name):
                v = getattr(self.__self, name)
                setattr(self, name, v)
                return v
            elif name in ('groupindex', 'groups'):
                return 0 if name == 'groupindex' else {}
            else:
                flag_attrs = (  # order by 2nd elt
                    ('hasIndices', 'd'),
                    ('global', 'g'),
                    ('ignoreCase', 'i'),
                    ('multiline', 'm'),
                    ('dotAll', 's'),
                    ('unicode', 'u'),
                    ('unicodeSets', 'v'),
                    ('sticky', 'y'),
                )
                for k, c in flag_attrs:
                    if name == k:
                        return bool(self.RE_FLAGS[c] & self.__flags)
                else:
                    if name == 'flags':
                        return ''.join(
                            (c if self.RE_FLAGS[c] & self.__flags else '')
                            for _, c in flag_attrs)

            raise AttributeError('{0} has no attribute named {1}'.format(self, name))