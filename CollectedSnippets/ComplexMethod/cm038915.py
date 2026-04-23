def collapse_argpool(self, *args, **kwargs):
        argpool_args = [arg for arg in args if isinstance(arg, ArgPool)] + [
            arg for arg in kwargs.values() if isinstance(arg, ArgPool)
        ]
        if len(argpool_args) == 0:
            return [args], [kwargs]

        # Make sure all argpools are of the same size
        argpool_size = len(argpool_args[0].values)
        assert all([argpool_size == len(arg.values) for arg in argpool_args])

        # create copies of the args
        args_list = []
        kwargs_list = []
        for _ in range(argpool_size):
            args_list.append(args)
            kwargs_list.append(kwargs.copy())

        for i in range(argpool_size):
            # collapse args; Just pick the ith value
            args_list[i] = tuple(
                [arg[i] if isinstance(arg, ArgPool) else arg for arg in args_list[i]]
            )

            # collapse kwargs
            kwargs_i = kwargs_list[i]
            arg_pool_keys = [k for k, v in kwargs_i.items() if isinstance(v, ArgPool)]
            for k in arg_pool_keys:
                # again just pick the ith value
                kwargs_i[k] = kwargs_i[k][i]
            kwargs_list[i] = kwargs_i

        return args_list, kwargs_list