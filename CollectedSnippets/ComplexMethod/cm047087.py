def __init__(self, *args, **kwargs):
        response = None
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, Response):
                response = arg._wrapped__
            elif isinstance(arg, _Response):
                response = arg
            elif isinstance(arg, werkzeug.wrappers.Response):
                response = _Response.load(arg)
        if response is None:
            if isinstance(kwargs.get('headers'), Headers):
                kwargs['headers'] = kwargs['headers']._wrapped__
            response = _Response(*args, **kwargs)

        super().__init__(response)
        if 'set_cookie' in response.__dict__:
            self.__dict__['set_cookie'] = response.__dict__['set_cookie']