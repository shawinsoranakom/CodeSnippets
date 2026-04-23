def _write(_arg_name, _arg_value):
            if _arg_name in self.operation.serialization_expand_args and isinstance(
                _arg_value, (list, tuple, dict)
            ):
                if isinstance(_arg_value, dict):
                    self.feed("%s={" % _arg_name)
                    self.indent()
                    for key, value in _arg_value.items():
                        key_string, key_imports = MigrationWriter.serialize(key)
                        arg_string, arg_imports = MigrationWriter.serialize(value)
                        args = arg_string.splitlines()
                        if len(args) > 1:
                            self.feed("%s: %s" % (key_string, args[0]))
                            for arg in args[1:-1]:
                                self.feed(arg)
                            self.feed("%s," % args[-1])
                        else:
                            self.feed("%s: %s," % (key_string, arg_string))
                        imports.update(key_imports)
                        imports.update(arg_imports)
                    self.unindent()
                    self.feed("},")
                else:
                    self.feed("%s=[" % _arg_name)
                    self.indent()
                    for item in _arg_value:
                        arg_string, arg_imports = MigrationWriter.serialize(item)
                        args = arg_string.splitlines()
                        if len(args) > 1:
                            for arg in args[:-1]:
                                self.feed(arg)
                            self.feed("%s," % args[-1])
                        else:
                            self.feed("%s," % arg_string)
                        imports.update(arg_imports)
                    self.unindent()
                    self.feed("],")
            else:
                arg_string, arg_imports = MigrationWriter.serialize(_arg_value)
                args = arg_string.splitlines()
                if len(args) > 1:
                    self.feed("%s=%s" % (_arg_name, args[0]))
                    for arg in args[1:-1]:
                        self.feed(arg)
                    self.feed("%s," % args[-1])
                else:
                    self.feed("%s=%s," % (_arg_name, arg_string))
                imports.update(arg_imports)