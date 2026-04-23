def _try_bind_args(fn, *args, **kwargs):
            fn_args = inspect.getargspec(fn)
            # Py2: ArgInfo(args, varargs, keywords, defaults)
            # Py3: ArgSpec(args, varargs, keywords, defaults)
            if not fn_args.keywords:
                for k in kwargs:
                    if k not in (fn_args.args or []):
                        raise TypeError("got an unexpected keyword argument: '{0}'".format(k))
            if not fn_args.varargs:
                args_to_bind = len(args)
                bindable = len(fn_args.args or [])
                if args_to_bind > bindable:
                    raise TypeError('too many positional arguments')
                bindable -= len(fn_args.defaults or [])
                if args_to_bind < bindable:
                    if kwargs:
                        bindable -= len(set(fn_args.args or []) & set(kwargs))
                    if bindable > args_to_bind:
                        raise TypeError("missing a required argument: '{0}'".format(fn_args.args[args_to_bind]))