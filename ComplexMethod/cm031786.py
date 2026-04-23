def generate(self, name: str, obj: object) -> str:
        # Use repr() in the key to distinguish -0.0 from +0.0
        key = (type(obj), obj, repr(obj))
        if key in self.cache:
            self.hits += 1
            # print(f"Cache hit {key!r:.40}: {self.cache[key]!r:.40}")
            return self.cache[key]
        self.misses += 1
        if isinstance(obj, types.CodeType) :
            val = self.generate_code(name, obj)
        elif isinstance(obj, tuple):
            val = self.generate_tuple(name, obj)
        elif isinstance(obj, str):
            val = self.generate_unicode(name, obj)
        elif isinstance(obj, bytes):
            val = self.generate_bytes(name, obj)
        elif obj is True:
            return "Py_True"
        elif obj is False:
            return "Py_False"
        elif isinstance(obj, int):
            val = self.generate_int(name, obj)
        elif isinstance(obj, float):
            val = self.generate_float(name, obj)
        elif isinstance(obj, complex):
            val = self.generate_complex(name, obj)
        elif isinstance(obj, frozenset):
            val = self.generate_frozenset(name, obj)
        elif obj is builtins.Ellipsis:
            return "Py_Ellipsis"
        elif obj is None:
            return "Py_None"
        else:
            raise TypeError(
                f"Cannot generate code for {type(obj).__name__} object")
        # print(f"Cache store {key!r:.40}: {val!r:.40}")
        self.cache[key] = val
        return val