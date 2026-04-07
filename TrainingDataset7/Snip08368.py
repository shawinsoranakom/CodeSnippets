def signal_connect_error(model_key, func, args, keywords):
        error_msg = (
            "%(receiver)s was connected to the '%(signal)s' signal with a "
            "lazy reference to the sender '%(model)s', but %(model_error)s."
        )
        receiver = args[0]
        # The receiver is either a function or an instance of class
        # defining a `__call__` method.
        if isinstance(receiver, types.FunctionType):
            description = "The function '%s'" % receiver.__name__
        elif isinstance(receiver, types.MethodType):
            description = "Bound method '%s.%s'" % (
                receiver.__self__.__class__.__name__,
                receiver.__name__,
            )
        else:
            description = "An instance of class '%s'" % receiver.__class__.__name__
        signal_name = model_signals.get(func.__self__, "unknown")
        params = {
            "model": ".".join(model_key),
            "receiver": description,
            "signal": signal_name,
            "model_error": app_model_error(model_key),
        }
        return Error(error_msg % params, obj=receiver.__module__, id="signals.E001")