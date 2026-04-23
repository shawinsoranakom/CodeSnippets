def devtools_wrapper(*args, **kwargs):
        if args and args[0].__class__.__name__ == 'DriverController':
            if get_conf('longpolling', section='devtools'):
                _logger.warning("Refusing call to %s: longpolling is disabled by devtools", fname)
                raise Locked("Longpolling disabled by devtools")  # raise to make the http request fail
        elif function.__name__ == 'action':
            action = args[1].get('action', 'default')  # first argument is self (containing Driver instance), second is 'data'
            disabled_actions = (get_conf('actions', section='devtools') or '').split(',')
            if action in disabled_actions or '*' in disabled_actions:
                _logger.warning("Ignoring call to %s: '%s' action is disabled by devtools", fname, action)
                return None
        elif get_conf('general', section='devtools'):
            _logger.warning("Ignoring call to %s: method is disabled by devtools", fname)
            return None

        return function(*args, **kwargs)