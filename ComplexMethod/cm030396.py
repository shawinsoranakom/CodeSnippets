def __enter__(self):
        """Perform the patch."""
        if self.is_started:
            raise RuntimeError("Patch is already started")

        new, spec, spec_set = self.new, self.spec, self.spec_set
        autospec, kwargs = self.autospec, self.kwargs
        new_callable = self.new_callable
        self.target = self.getter()

        # normalise False to None
        if spec is False:
            spec = None
        if spec_set is False:
            spec_set = None
        if autospec is False:
            autospec = None

        if spec is not None and autospec is not None:
            raise TypeError("Can't specify spec and autospec")
        if ((spec is not None or autospec is not None) and
            spec_set not in (True, None)):
            raise TypeError("Can't provide explicit spec_set *and* spec or autospec")

        original, local = self.get_original()

        if new is DEFAULT and autospec is None:
            inherit = False
            if spec is True:
                # set spec to the object we are replacing
                spec = original
                if spec_set is True:
                    spec_set = original
                    spec = None
            elif spec is not None:
                if spec_set is True:
                    spec_set = spec
                    spec = None
            elif spec_set is True:
                spec_set = original

            if spec is not None or spec_set is not None:
                if original is DEFAULT:
                    raise TypeError("Can't use 'spec' with create=True")
                if isinstance(original, type):
                    # If we're patching out a class and there is a spec
                    inherit = True

            # Determine the Klass to use
            if new_callable is not None:
                Klass = new_callable
            elif spec is None and _is_async_obj(original):
                Klass = AsyncMock
            elif spec is not None or spec_set is not None:
                this_spec = spec
                if spec_set is not None:
                    this_spec = spec_set
                if _is_list(this_spec):
                    not_callable = '__call__' not in this_spec
                else:
                    not_callable = not callable(this_spec)
                if _is_async_obj(this_spec):
                    Klass = AsyncMock
                elif not_callable:
                    Klass = NonCallableMagicMock
                else:
                    Klass = MagicMock
            else:
                Klass = MagicMock

            _kwargs = {}
            if spec is not None:
                _kwargs['spec'] = spec
            if spec_set is not None:
                _kwargs['spec_set'] = spec_set

            # add a name to mocks
            if (isinstance(Klass, type) and
                issubclass(Klass, NonCallableMock) and self.attribute):
                _kwargs['name'] = self.attribute

            _kwargs.update(kwargs)
            new = Klass(**_kwargs)

            if inherit and _is_instance_mock(new):
                # we can only tell if the instance should be callable if the
                # spec is not a list
                this_spec = spec
                if spec_set is not None:
                    this_spec = spec_set
                if (not _is_list(this_spec) and not
                    _instance_callable(this_spec)):
                    Klass = NonCallableMagicMock

                _kwargs.pop('name')
                new.return_value = Klass(_new_parent=new, _new_name='()',
                                         **_kwargs)
        elif autospec is not None:
            # spec is ignored, new *must* be default, spec_set is treated
            # as a boolean. Should we check spec is not None and that spec_set
            # is a bool?
            if new is not DEFAULT:
                raise TypeError(
                    "autospec creates the mock for you. Can't specify "
                    "autospec and new."
                )
            if original is DEFAULT:
                raise TypeError("Can't use 'autospec' with create=True")
            spec_set = bool(spec_set)
            if autospec is True:
                autospec = original

            if _is_instance_mock(self.target):
                raise InvalidSpecError(
                    f'Cannot autospec attr {self.attribute!r} as the patch '
                    f'target has already been mocked out. '
                    f'[target={self.target!r}, attr={autospec!r}]')
            if _is_instance_mock(autospec):
                target_name = getattr(self.target, '__name__', self.target)
                raise InvalidSpecError(
                    f'Cannot autospec attr {self.attribute!r} from target '
                    f'{target_name!r} as it has already been mocked out. '
                    f'[target={self.target!r}, attr={autospec!r}]')

            new = create_autospec(autospec, spec_set=spec_set,
                                  _name=self.attribute, **kwargs)
        elif kwargs:
            # can't set keyword args when we aren't creating the mock
            # XXXX If new is a Mock we could call new.configure_mock(**kwargs)
            raise TypeError("Can't pass kwargs to a mock we aren't creating")

        new_attr = new

        self.temp_original = original
        self.is_local = local
        self._exit_stack = contextlib.ExitStack()
        self.is_started = True
        try:
            setattr(self.target, self.attribute, new_attr)
            if self.attribute_name is not None:
                extra_args = {}
                if self.new is DEFAULT:
                    extra_args[self.attribute_name] =  new
                for patching in self.additional_patchers:
                    arg = self._exit_stack.enter_context(patching)
                    if patching.new is DEFAULT:
                        extra_args.update(arg)
                return extra_args

            return new
        except:
            if not self.__exit__(*sys.exc_info()):
                raise