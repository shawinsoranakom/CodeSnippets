def save_global(self, obj, name=None):
        write = self.write

        if name is None:
            name = getattr(obj, '__qualname__', None)
            if name is None:
                name = obj.__name__

        if '.__' in name:
            # Mangle names of private attributes.
            dotted_path = name.split('.')
            for i, subpath in enumerate(dotted_path):
                if i and subpath.startswith('__') and not subpath.endswith('__'):
                    prev = prev.lstrip('_')
                    if prev:
                        dotted_path[i] = f"_{prev.lstrip('_')}{subpath}"
                prev = subpath
            name = '.'.join(dotted_path)

        module_name = whichmodule(obj, name)
        if self.proto >= 2:
            code = _extension_registry.get((module_name, name), _NoValue)
            if code is not _NoValue:
                if code <= 0xff:
                    data = pack("<B", code)
                    if data == b'\0':
                        # Should never happen in normal circumstances,
                        # since the type and the value of the code are
                        # checked in copyreg.add_extension().
                        raise RuntimeError("extension code 0 is out of range")
                    write(EXT1 + data)
                elif code <= 0xffff:
                    write(EXT2 + pack("<H", code))
                else:
                    write(EXT4 + pack("<i", code))
                return

        if self.proto >= 4:
            self.save(module_name)
            self.save(name)
            write(STACK_GLOBAL)
        elif '.' in name:
            # In protocol < 4, objects with multi-part __qualname__
            # are represented as
            # getattr(getattr(..., attrname1), attrname2).
            dotted_path = name.split('.')
            name = dotted_path.pop(0)
            save = self.save
            for attrname in dotted_path:
                save(getattr)
                if self.proto < 2:
                    write(MARK)
            self._save_toplevel_by_name(module_name, name)
            for attrname in dotted_path:
                save(attrname)
                if self.proto < 2:
                    write(TUPLE)
                else:
                    write(TUPLE2)
                write(REDUCE)
        else:
            self._save_toplevel_by_name(module_name, name)

        self.memoize(obj)