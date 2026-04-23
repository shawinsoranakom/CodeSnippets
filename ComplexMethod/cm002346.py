def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """When visiting imports from modeling files (i.e. `transformers.models.xxx`) we get the code, parse it,
        and save it in `self.model_specific_modules` to later visit. The imported objects are saved in `self.model_specific_imported_objects`.
        """
        # `node.module` is None for fully relative imports, e.g. `from ... import initialization as init`
        import_module = self.python_module.code_for_node(node.module) if node.module is not None else ""
        import_statement = "." * len(node.relative) + import_module
        if any(import_to_skip in import_statement for import_to_skip in IMPORTS_TO_SKIP_IN_MODULAR):
            return
        if m.matches(node.module, m.Attribute()):
            for imported_ in node.names:
                # If we match here, it's an import from 3rd party lib that we need to skip
                if any(external_file["name"] in import_statement for external_file in self.excluded_external_files):
                    continue
                _import = re.search(
                    rf"(?:transformers\.models\.)|(?:\.\.\.models\.)|(?:\.\.)\w+\.({self.match_patterns}).*",
                    import_statement,
                )
                if _import:
                    source = _import.group(1)
                    if source == "modeling" and "Config" in self.python_module.code_for_node(imported_):
                        raise ValueError(
                            f"You are importing {self.python_module.code_for_node(imported_)} from the modeling file. Import from the `configuration_xxxx.py` file instead"
                        )
                    if import_module not in self.model_specific_modules:
                        if "models" not in import_module:
                            import_module = "models." + import_module
                        if not import_module.startswith("transformers"):
                            import_module = "transformers." + import_module
                        try:
                            source_code = get_module_source_from_name(import_module)
                        except ModuleNotFoundError as e:
                            raise ModuleNotFoundError(
                                f"Failed to visit import from for: {self.python_module.code_for_node(node)}. Tried to import {import_module} but failed."
                            ) from e
                        tree = cst.parse_module(source_code)
                        self.model_specific_modules[import_module] = tree
                    imported_object = self.python_module.code_for_node(imported_.name)
                    self.model_specific_imported_objects[imported_object] = import_module
        if m.matches(node.module, m.Name()):
            if import_module == "transformers":
                raise ValueError(
                    f"You are importing from {import_module} directly using global imports. Import from the correct local path"
                )