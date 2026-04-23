def test_transformers_specific_model_import(self):
        """
        This test ensures that there is equivalence between what is written down in __all__ and what is
        written down with register().

        It doesn't test the backends attributed to register().
        """
        for architecture in os.listdir(self.models_path):
            if (
                os.path.isfile(self.models_path / architecture)
                or architecture.startswith("_")
                or architecture == "deprecated"
            ):
                continue

            with self.subTest(f"Testing arch {architecture}"):
                import_structure = define_import_structure(self.models_path / architecture)
                backend_agnostic_import_structure = {}
                for module_object_mapping in import_structure.values():
                    for module, objects in module_object_mapping.items():
                        if module not in backend_agnostic_import_structure:
                            backend_agnostic_import_structure[module] = []

                        backend_agnostic_import_structure[module].extend(objects)

                for module, objects in backend_agnostic_import_structure.items():
                    with open(self.models_path / architecture / f"{module}.py") as f:
                        content = f.read()
                        _all = fetch__all__(content)

                        if _all is None:
                            raise ValueError(f"{module} doesn't have __all__ defined.")

                        error_message = (
                            f"self.models_path / architecture / f'{module}.py doesn't seem to be defined correctly:\n"
                            f"Defined in __all__: {sorted(_all)}\nDefined with register: {sorted(objects)}"
                        )
                        self.assertListEqual(sorted(objects), sorted(_all), msg=error_message)