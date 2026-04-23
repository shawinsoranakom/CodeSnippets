def _showtraceback(self, typ, value, tb, source):
        sys.last_type = typ
        sys.last_traceback = tb
        value = value.with_traceback(tb)
        # Set the line of text that the exception refers to
        lines = source.splitlines()
        if (source and typ is SyntaxError
                and not value.text and value.lineno is not None
                and len(lines) >= value.lineno):
            value.text = lines[value.lineno - 1]
        sys.last_exc = sys.last_value = value
        if sys.excepthook is sys.__excepthook__:
            self._excepthook(typ, value, tb)
        else:
            # If someone has set sys.excepthook, we let that take precedence
            # over self.write
            try:
                sys.excepthook(typ, value, tb)
            except SystemExit:
                raise
            except BaseException as e:
                e.__context__ = None
                e = e.with_traceback(e.__traceback__.tb_next)
                print('Error in sys.excepthook:', file=sys.stderr)
                sys.__excepthook__(type(e), e, e.__traceback__)
                print(file=sys.stderr)
                print('Original exception was:', file=sys.stderr)
                sys.__excepthook__(typ, value, tb)