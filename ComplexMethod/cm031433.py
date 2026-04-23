def configure_handler(self, config):
        """Configure a handler from a dictionary."""
        config_copy = dict(config)  # for restoring in case of error
        formatter = config.pop('formatter', None)
        if formatter:
            try:
                formatter = self.config['formatters'][formatter]
            except Exception as e:
                raise ValueError('Unable to set formatter '
                                 '%r' % formatter) from e
        level = config.pop('level', None)
        filters = config.pop('filters', None)
        if '()' in config:
            c = config.pop('()')
            if not callable(c):
                c = self.resolve(c)
            factory = c
        else:
            cname = config.pop('class')
            if callable(cname):
                klass = cname
            else:
                klass = self.resolve(cname)
            if issubclass(klass, logging.handlers.MemoryHandler):
                if 'flushLevel' in config:
                    config['flushLevel'] = logging._checkLevel(config['flushLevel'])
                if 'target' in config:
                    # Special case for handler which refers to another handler
                    try:
                        tn = config['target']
                        th = self.config['handlers'][tn]
                        if not isinstance(th, logging.Handler):
                            config.update(config_copy)  # restore for deferred cfg
                            raise TypeError('target not configured yet')
                        config['target'] = th
                    except Exception as e:
                        raise ValueError('Unable to set target handler %r' % tn) from e
            elif issubclass(klass, logging.handlers.QueueHandler):
                # Another special case for handler which refers to other handlers
                # if 'handlers' not in config:
                    # raise ValueError('No handlers specified for a QueueHandler')
                if 'queue' in config:
                    qspec = config['queue']

                    if isinstance(qspec, str):
                        q = self.resolve(qspec)
                        if not callable(q):
                            raise TypeError('Invalid queue specifier %r' % qspec)
                        config['queue'] = q()
                    elif isinstance(qspec, dict):
                        if '()' not in qspec:
                            raise TypeError('Invalid queue specifier %r' % qspec)
                        config['queue'] = self.configure_custom(dict(qspec))
                    elif not _is_queue_like_object(qspec):
                        raise TypeError('Invalid queue specifier %r' % qspec)

                if 'listener' in config:
                    lspec = config['listener']
                    if isinstance(lspec, type):
                        if not issubclass(lspec, logging.handlers.QueueListener):
                            raise TypeError('Invalid listener specifier %r' % lspec)
                    else:
                        if isinstance(lspec, str):
                            listener = self.resolve(lspec)
                            if isinstance(listener, type) and\
                                not issubclass(listener, logging.handlers.QueueListener):
                                raise TypeError('Invalid listener specifier %r' % lspec)
                        elif isinstance(lspec, dict):
                            if '()' not in lspec:
                                raise TypeError('Invalid listener specifier %r' % lspec)
                            listener = self.configure_custom(dict(lspec))
                        else:
                            raise TypeError('Invalid listener specifier %r' % lspec)
                        if not callable(listener):
                            raise TypeError('Invalid listener specifier %r' % lspec)
                        config['listener'] = listener
                if 'handlers' in config:
                    hlist = []
                    try:
                        for hn in config['handlers']:
                            h = self.config['handlers'][hn]
                            if not isinstance(h, logging.Handler):
                                config.update(config_copy)  # restore for deferred cfg
                                raise TypeError('Required handler %r '
                                                'is not configured yet' % hn)
                            hlist.append(h)
                    except Exception as e:
                        raise ValueError('Unable to set required handler %r' % hn) from e
                    config['handlers'] = hlist
            elif issubclass(klass, logging.handlers.SMTPHandler) and\
                'mailhost' in config:
                config['mailhost'] = self.as_tuple(config['mailhost'])
            elif issubclass(klass, logging.handlers.SysLogHandler) and\
                'address' in config:
                config['address'] = self.as_tuple(config['address'])
            if issubclass(klass, logging.handlers.QueueHandler):
                factory = functools.partial(self._configure_queue_handler, klass)
            else:
                factory = klass
        kwargs = {k: config[k] for k in config if (k != '.' and valid_ident(k))}
        # When deprecation ends for using the 'strm' parameter, remove the
        # "except TypeError ..."
        try:
            result = factory(**kwargs)
        except TypeError as te:
            if "'stream'" not in str(te):
                raise
            #The argument name changed from strm to stream
            #Retry with old name.
            #This is so that code can be used with older Python versions
            #(e.g. by Django)
            kwargs['strm'] = kwargs.pop('stream')
            result = factory(**kwargs)

            import warnings
            warnings.warn(
                "Support for custom logging handlers with the 'strm' argument "
                "is deprecated and scheduled for removal in Python 3.16. "
                "Define handlers with the 'stream' argument instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if formatter:
            result.setFormatter(formatter)
        if level is not None:
            result.setLevel(logging._checkLevel(level))
        if filters:
            self.add_filters(result, filters)
        props = config.pop('.', None)
        if props:
            for name, value in props.items():
                setattr(result, name, value)
        return result