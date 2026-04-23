def __init__(self, code: (str | SQL) = "", /, *args, to_flush: (Field | Iterable[Field] | None) = None, **kwargs):
        if isinstance(code, SQL):
            if args or kwargs or to_flush:
                raise TypeError("SQL() unexpected arguments when code has type SQL")
            self.__code = code.__code
            self.__params = code.__params
            self.__to_flush = code.__to_flush
            return

        # validate the format of code and parameters
        if args and kwargs:
            raise TypeError("SQL() takes either positional arguments, or named arguments")

        if kwargs:
            code, args = named_to_positional_printf(code, kwargs)
        elif not args:
            code % ()  # check that code does not contain %s
            self.__code = code
            self.__params = ()
            if to_flush is None:
                self.__to_flush = ()
            elif hasattr(to_flush, '__iter__'):
                self.__to_flush = tuple(to_flush)
            else:
                self.__to_flush = (to_flush,)
            return

        code_list = []
        params_list = []
        to_flush_list = []
        for arg in args:
            if isinstance(arg, SQL):
                code_list.append(arg.__code)
                params_list.extend(arg.__params)
                to_flush_list.extend(arg.__to_flush)
            else:
                code_list.append("%s")
                params_list.append(arg)
        if to_flush is not None:
            if hasattr(to_flush, '__iter__'):
                to_flush_list.extend(to_flush)
            else:
                to_flush_list.append(to_flush)

        self.__code = code.replace('%%', '%%%%') % tuple(code_list)
        self.__params = tuple(params_list)
        self.__to_flush = tuple(to_flush_list)