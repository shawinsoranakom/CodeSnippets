def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluable in self.namespace, it will be evaluated and its attributes
        (as revealed by dir()) are used as possible completions.  (For class
        instances, class members are also considered.)

        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.

        """
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            return []
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            return []

        # get the content of the object, except __builtins__
        words = set(dir(thisobject))
        words.discard("__builtins__")

        if hasattr(thisobject, '__class__'):
            words.add('__class__')
            words.update(get_class_members(thisobject.__class__))
        matches = []
        n = len(attr)
        if attr == '':
            noprefix = '_'
        elif attr == '_':
            noprefix = '__'
        else:
            noprefix = None
        while True:
            for word in words:
                if (word[:n] == attr and
                    not (noprefix and word[:n+1] == noprefix)):
                    match = "%s.%s" % (expr, word)
                    if isinstance(getattr(type(thisobject), word, None),
                                  property):
                        # bpo-44752: thisobject.word is a method decorated by
                        # `@property`. What follows applies a postfix if
                        # thisobject.word is callable, but know we know that
                        # this is not callable (because it is a property).
                        # Also, getattr(thisobject, word) will evaluate the
                        # property method, which is not desirable.
                        matches.append(match)
                        continue

                    if (isinstance(thisobject, types.ModuleType)
                        and
                        isinstance(thisobject.__dict__.get(word),
                                   types.LazyImportType)
                    ):
                        value = thisobject.__dict__.get(word)
                    else:
                        value = getattr(thisobject, word, None)

                    if value is not None:
                        matches.append(self._callable_postfix(value, match))
                    else:
                        matches.append(match)
            if matches or not noprefix:
                break
            if noprefix == '_':
                noprefix = '__'
            else:
                noprefix = None
        matches.sort()
        return matches