def _attr_matches(self, text):
        expr, attr = text.rsplit('.', 1)
        if '(' in expr or ')' in expr:  # don't call functions
            return expr, attr, [], []
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return expr, attr, [], []

        # get the content of the object, except __builtins__
        words = set(dir(thisobject)) - {'__builtins__'}

        if hasattr(thisobject, '__class__'):
            words.add('__class__')
            words.update(rlcompleter.get_class_members(thisobject.__class__))
        names = []
        values = []
        n = len(attr)
        if attr == '':
            noprefix = '_'
        elif attr == '_':
            noprefix = '__'
        else:
            noprefix = None

        # sort the words now to make sure to return completions in
        # alphabetical order. It's easier to do it now, else we would need to
        # sort 'names' later but make sure that 'values' in kept in sync,
        # which is annoying.
        words = sorted(words)
        while True:
            for word in words:
                if (
                    word[:n] == attr
                    and not (noprefix and word[:n+1] == noprefix)
                ):
                    # Mirror rlcompleter's safeguards so completion does not
                    # call properties or reify lazy module attributes.
                    if isinstance(getattr(type(thisobject), word, None), property):
                        value = None
                    elif (
                        isinstance(thisobject, types.ModuleType)
                        and isinstance(
                            thisobject.__dict__.get(word),
                            types.LazyImportType,
                        )
                    ):
                        value = thisobject.__dict__.get(word)
                    else:
                        value = getattr(thisobject, word, None)

                    names.append(word)
                    values.append(value)
            if names or not noprefix:
                break
            if noprefix == '_':
                noprefix = '__'
            else:
                noprefix = None

        return expr, attr, names, values