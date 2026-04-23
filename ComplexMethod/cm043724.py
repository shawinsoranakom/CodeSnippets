def test_provider_field_dupes(self):
        """Check for duplicate fields in the provider models.

        This function checks for duplicate fields in the provider models
        and identifies the fields that should be standardized.
        """
        standard_models_directory = os.path.dirname(standard_models.__file__)
        standard_models_files = glob.glob(
            os.path.join(standard_models_directory, "*.py")
        )

        standard_query_classes = get_subclasses(
            standard_models_files, standard_models.__name__, QueryParams
        )
        standard_data_classes = get_subclasses(
            standard_models_files, standard_models.__name__, Data
        )

        provider_modules = get_provider_modules()

        child_parent_dict = {}

        for module in provider_modules:
            provider_module = importlib.import_module(module)

            # query classes
            child_parent_map(child_parent_dict, standard_query_classes, provider_module)

            # data classes
            child_parent_map(child_parent_dict, standard_data_classes, provider_module)

        # remove keys with no values
        child_parent_dict = {k: v for k, v in child_parent_dict.items() if v}

        for std_cls in child_parent_dict:
            with self.subTest(i=std_cls):
                providers_w_fields_raw = child_parent_dict[std_cls]

                # remove duplicate keys
                providers_w_fields = []
                keys = []
                for item in providers_w_fields_raw:
                    k = list(item.keys())[0]
                    if k not in keys:
                        keys.append(k)
                        providers_w_fields.append(item)

                fields = []
                provider_models = []

                for provider_cls in providers_w_fields:
                    provider_models.extend(list(provider_cls.keys()))
                    fields.extend(list(provider_cls.values())[0])

                seen = set()
                dupes = [x for x in fields if x in seen or seen.add(x)]

                dupes_str = ", ".join([f"'{x}'" for x in set(dupes)])
                provider_str = (
                    ", ".join(match_provider_and_fields(providers_w_fields, set(dupes)))
                    if dupes
                    else ""
                )

                assert not dupes, (
                    f"The following fields are common among models and should be standardized: {dupes_str}.\n"
                    f"Standard model: {std_cls}, Provider models: {provider_str}\n"
                )