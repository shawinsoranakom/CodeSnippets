def __init__(
        self,
        name: str,
        module_file: str,
        import_structure: IMPORT_STRUCTURE_T,
        module_spec: importlib.machinery.ModuleSpec | None = None,
        extra_objects: dict[str, object] | None = None,
        explicit_import_shortcut: dict[str, list[str]] | None = None,
    ):
        super().__init__(name)

        self._object_missing_backend = {}
        self._explicit_import_shortcut = explicit_import_shortcut if explicit_import_shortcut else {}

        if any(isinstance(key, frozenset) for key in import_structure):
            self._modules = set()
            self._class_to_module = {}
            self.__all__ = []

            _import_structure = {}

            for backends, module in import_structure.items():
                missing_backends = []

                # This ensures that if a module is importable, then all other keys of the module are importable.
                # As an example, in module.keys() we might have the following:
                #
                # dict_keys(['models.nllb_moe.configuration_nllb_moe', 'models.sew_d.configuration_sew_d'])
                #
                # with this, we don't only want to be able to import these explicitly, we want to be able to import
                # every intermediate module as well. Therefore, this is what is returned:
                #
                # {
                #     'models.nllb_moe.configuration_nllb_moe',
                #     'models.sew_d.configuration_sew_d',
                #     'models',
                #     'models.sew_d', 'models.nllb_moe'
                # }

                module_keys = set(
                    chain(*[[k.rsplit(".", i)[0] for i in range(k.count(".") + 1)] for k in list(module.keys())])
                )

                for backend in backends:
                    if backend in BACKENDS_MAPPING:
                        callable, _ = BACKENDS_MAPPING[backend]
                    else:
                        if any(key in backend for key in ["=", "<", ">"]):
                            backend = Backend(backend)
                            callable = backend.is_satisfied
                        else:
                            raise ValueError(
                                f"Backend should be defined in the BACKENDS_MAPPING. Offending backend: {backend}"
                            )

                    try:
                        if not callable():
                            missing_backends.append(backend)
                    except (ModuleNotFoundError, RuntimeError):
                        missing_backends.append(backend)

                self._modules = self._modules.union(module_keys)

                for key, values in module.items():
                    if missing_backends:
                        self._object_missing_backend[key] = missing_backends

                    for value in values:
                        self._class_to_module[value] = key
                        if missing_backends:
                            self._object_missing_backend[value] = missing_backends
                    _import_structure.setdefault(key, []).extend(values)

                # Needed for autocompletion in an IDE
                self.__all__.extend(module_keys | set(chain(*module.values())))

            self.__file__ = module_file
            self.__spec__ = module_spec
            self.__path__ = [os.path.dirname(module_file)]
            self._objects = {} if extra_objects is None else extra_objects
            self._name = name
            self._import_structure = _import_structure

        # This can be removed once every exportable object has a `require()` require.
        else:
            self._modules = set(import_structure.keys())
            self._class_to_module = {}
            for key, values in import_structure.items():
                for value in values:
                    self._class_to_module[value] = key
            # Needed for autocompletion in an IDE
            self.__all__ = list(import_structure.keys()) + list(chain(*import_structure.values()))
            self.__file__ = module_file
            self.__spec__ = module_spec
            self.__path__ = [os.path.dirname(module_file)]
            self._objects = {} if extra_objects is None else extra_objects
            self._name = name
            self._import_structure = import_structure