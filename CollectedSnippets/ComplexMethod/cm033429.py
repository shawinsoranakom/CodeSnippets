def process_args(input_arguments):
        no_arguments = []
        error_arguments = []
        for arg in args:
            if arg not in input_arguments:
                no_arguments.append(arg)
        for k, v in kwargs.items():
            config_value = input_arguments.get(k, None)
            if config_value is None:
                no_arguments.append(k)
            elif isinstance(v, (tuple, list)):
                if config_value not in v:
                    error_arguments.append((k, set(v)))
            elif config_value != v:
                error_arguments.append((k, v))
        if no_arguments or error_arguments:
            error_string = ""
            if no_arguments:
                error_string += "required argument are missing: {}; ".format(",".join(no_arguments))
            if error_arguments:
                error_string += "required argument values: {}".format(",".join(["{}={}".format(a[0], a[1]) for a in error_arguments]))
            return error_string
        return None