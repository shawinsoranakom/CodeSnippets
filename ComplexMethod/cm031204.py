def _fix_up_module(cls, module):
        spec = module.__spec__
        state = spec.loader_state
        if state is None:
            # The module is missing FrozenImporter-specific values.

            # Fix up the spec attrs.
            origname = vars(module).pop('__origname__', None)
            assert origname, 'see PyImport_ImportFrozenModuleObject()'
            ispkg = hasattr(module, '__path__')
            assert _imp.is_frozen_package(module.__name__) == ispkg, ispkg
            filename, pkgdir = cls._resolve_filename(origname, spec.name, ispkg)
            spec.loader_state = type(sys.implementation)(
                filename=filename,
                origname=origname,
            )
            __path__ = spec.submodule_search_locations
            if ispkg:
                assert __path__ == [], __path__
                if pkgdir:
                    spec.submodule_search_locations.insert(0, pkgdir)
            else:
                assert __path__ is None, __path__

            # Fix up the module attrs (the bare minimum).
            assert not hasattr(module, '__file__'), module.__file__
            if filename:
                try:
                    module.__file__ = filename
                except AttributeError:
                    pass
            if ispkg:
                if module.__path__ != __path__:
                    assert module.__path__ == [], module.__path__
                    module.__path__.extend(__path__)
        else:
            # These checks ensure that _fix_up_module() is only called
            # in the right places.
            __path__ = spec.submodule_search_locations
            ispkg = __path__ is not None
            # Check the loader state.
            assert sorted(vars(state)) == ['filename', 'origname'], state
            if state.origname:
                # The only frozen modules with "origname" set are stdlib modules.
                (__file__, pkgdir,
                 ) = cls._resolve_filename(state.origname, spec.name, ispkg)
                assert state.filename == __file__, (state.filename, __file__)
                if pkgdir:
                    assert __path__ == [pkgdir], (__path__, pkgdir)
                else:
                    assert __path__ == ([] if ispkg else None), __path__
            else:
                __file__ = None
                assert state.filename is None, state.filename
                assert __path__ == ([] if ispkg else None), __path__
            # Check the file attrs.
            if __file__:
                assert hasattr(module, '__file__')
                assert module.__file__ == __file__, (module.__file__, __file__)
            else:
                assert not hasattr(module, '__file__'), module.__file__
            if ispkg:
                assert hasattr(module, '__path__')
                assert module.__path__ == __path__, (module.__path__, __path__)
            else:
                assert not hasattr(module, '__path__'), module.__path__
        assert not spec.has_location