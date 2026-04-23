def save_pickle(
        self,
        package: str,
        resource: str,
        obj: Any,
        dependencies: bool = True,
        pickle_protocol: int = 3,
    ):
        """Save a python object to the archive using pickle. Equivalent to :func:`torch.save` but saving into
        the archive rather than a stand-alone file. Standard pickle does not save the code, only the objects.
        If ``dependencies`` is true, this method will also scan the pickled objects for which modules are required
        to reconstruct them and save the relevant code.

        To be able to save an object where ``type(obj).__name__`` is ``my_module.MyObject``,
        ``my_module.MyObject`` must resolve to the class of the object according to the ``importer`` order. When saving objects that
        have previously been packaged, the importer's ``import_module`` method will need to be present in the ``importer`` list
        for this to work.

        Args:
            package (str): The name of module package this resource should go in (e.g. ``"my_package.my_subpackage"``).
            resource (str): A unique name for the resource, used to identify it to load.
            obj (Any): The object to save, must be picklable.
            dependencies (bool, optional): If ``True``, we scan the source for dependencies.
        """

        if pickle_protocol not in (3, 4):
            raise AssertionError(
                f"torch.package only supports pickle protocols 3 and 4, got {pickle_protocol}"
            )

        filename = self._filename(package, resource)
        # Write the pickle data for `obj`
        data_buf = io.BytesIO()
        pickler = create_pickler(data_buf, self.importer, protocol=pickle_protocol)
        pickler.persistent_id = self._persistent_id
        pickler.dump(obj)
        data_value = data_buf.getvalue()
        mocked_modules = defaultdict(list)
        name_in_dependency_graph = f"<{package}.{resource}>"
        self.dependency_graph.add_node(
            name_in_dependency_graph,
            action=_ModuleProviderAction.INTERN,
            provided=True,
            is_pickle=True,
        )

        def _check_mocked_error(module: str | None, field: str | None):
            """
            checks if an object (field) comes from a mocked module and then adds
            the pair to mocked_modules which contains mocked modules paired with their
            list of mocked objects present in the pickle.

            We also hold the invariant that the first user defined rule that applies
            to the module is the one we use.
            """

            if not isinstance(module, str):
                raise AssertionError(f"module must be str, got {type(module).__name__}")
            if not isinstance(field, str):
                raise AssertionError(f"field must be str, got {type(field).__name__}")
            if self._can_implicitly_extern(module):
                return
            for pattern, pattern_info in self.patterns.items():
                if pattern.matches(module):
                    if pattern_info.action == _ModuleProviderAction.MOCK:
                        mocked_modules[module].append(field)
                    return

        if dependencies:
            all_dependencies = []
            module = None
            field = None
            memo: defaultdict[int, str] = defaultdict(None)
            memo_count = 0
            # pickletools.dis(data_value)
            # pyrefly: ignore [bad-assignment]
            for opcode, arg, _pos in pickletools.genops(data_value):
                if pickle_protocol == 4:
                    if (
                        opcode.name == "SHORT_BINUNICODE"
                        or opcode.name == "BINUNICODE"
                        or opcode.name == "BINUNICODE8"
                    ):
                        if not isinstance(arg, str):
                            raise AssertionError(
                                f"expected str arg for {opcode.name}, got {type(arg).__name__}"
                            )
                        module = field
                        field = arg
                        memo[memo_count] = arg
                    elif (
                        opcode.name == "LONG_BINGET"
                        or opcode.name == "BINGET"
                        or opcode.name == "GET"
                    ):
                        if not isinstance(arg, int):
                            raise AssertionError(
                                f"expected int arg for {opcode.name}, got {type(arg).__name__}"
                            )
                        module = field
                        field = memo.get(arg, None)
                    elif opcode.name == "MEMOIZE":
                        memo_count += 1
                    elif opcode.name == "STACK_GLOBAL":
                        if module is None:
                            # If not module was passed on in the entries preceding this one, continue.
                            continue
                        if not isinstance(module, str):
                            raise AssertionError(
                                f"module must be str, got {type(module).__name__}"
                            )
                        if module not in all_dependencies:
                            all_dependencies.append(module)
                        _check_mocked_error(module, field)
                elif (
                    pickle_protocol == 3 and opcode.name == "GLOBAL"
                ):  # a global reference
                    if not isinstance(arg, str):
                        raise AssertionError(
                            f"expected str arg for GLOBAL, got {type(arg).__name__}"
                        )
                    module, field = arg.split(" ")
                    if module not in all_dependencies:
                        all_dependencies.append(module)
                    _check_mocked_error(module, field)
            for module_name in all_dependencies:
                self.dependency_graph.add_edge(name_in_dependency_graph, module_name)

                """ If an object happens to come from a mocked module, then we collect these errors and spit them
                    out with the other errors found by package exporter.
                """
                if module_name in mocked_modules:
                    if not isinstance(module_name, str):
                        raise AssertionError(
                            f"module_name must be str, got {type(module_name).__name__}"
                        )
                    fields = mocked_modules[module_name]
                    self.dependency_graph.add_node(
                        module_name,
                        action=_ModuleProviderAction.MOCK,
                        error=PackagingErrorReason.MOCKED_BUT_STILL_USED,
                        error_context=f"Object(s) '{fields}' from module `{module_name}` was mocked out during packaging "
                        f"but is being used in resource - `{resource}` in package `{package}`. ",
                        provided=True,
                    )
                else:
                    self.add_dependency(module_name)

        self._write(filename, data_value)