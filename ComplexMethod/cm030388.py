def _mock_add_spec(self, spec, spec_set, _spec_as_instance=False,
                       _eat_self=False):
        if _is_instance_mock(spec):
            raise InvalidSpecError(f'Cannot spec a Mock object. [object={spec!r}]')

        _spec_class = None
        _spec_signature = None
        _spec_asyncs = []

        if spec is not None and not _is_list(spec):
            if isinstance(spec, type):
                _spec_class = spec
            else:
                _spec_class = type(spec)
            res = _get_signature_object(spec,
                                        _spec_as_instance, _eat_self)
            _spec_signature = res and res[1]

            spec_list = dir(spec)

            for attr in spec_list:
                static_attr = inspect.getattr_static(spec, attr, None)
                unwrapped_attr = static_attr
                try:
                    unwrapped_attr = inspect.unwrap(unwrapped_attr)
                except ValueError:
                    pass
                if iscoroutinefunction(unwrapped_attr):
                    _spec_asyncs.append(attr)

            spec = spec_list

        __dict__ = self.__dict__
        __dict__['_spec_class'] = _spec_class
        __dict__['_spec_set'] = spec_set
        __dict__['_spec_signature'] = _spec_signature
        __dict__['_mock_methods'] = spec
        __dict__['_spec_asyncs'] = _spec_asyncs