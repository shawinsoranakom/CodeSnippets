def parseTemplateYaml(self, yaml_file: str) -> None:
        with open(yaml_file) as f:
            contents = yaml.load(f, Loader=UniqueKeyLoader)
            for template_name, params_dict in contents.items():
                if template_name in self.shader_template_params:
                    raise KeyError(f"{template_name} params file is defined twice")

                default_params = params_dict["parameter_names_with_default_values"]
                params_names = set(default_params.keys()).union({"NAME"})

                self.shader_template_params[template_name] = []

                default_iterated_params = params_dict.get(
                    "generate_variant_forall", None
                )

                for variant in params_dict["shader_variants"]:
                    variant_params_names = set(variant.keys())
                    invalid_keys = (
                        variant_params_names
                        - params_names
                        - {"generate_variant_forall"}
                    )
                    if len(invalid_keys) != 0:
                        raise AssertionError(f"Invalid keys found: {invalid_keys}")

                    iterated_params = variant.get(
                        "generate_variant_forall", default_iterated_params
                    )

                    if iterated_params is not None:
                        variant_combinations = self.generateVariantCombinations(
                            iterated_params, variant_params_names
                        )

                        for combination in variant_combinations:
                            default_params_copy = copy.deepcopy(default_params)
                            for key in variant:
                                if key != "generate_variant_forall":
                                    default_params_copy[key] = variant[key]

                            variant_name = variant["NAME"]
                            for param_value in combination:
                                default_params_copy[param_value[0]] = param_value[2]
                                if len(param_value[1]) > 0:
                                    variant_name = f"{variant_name}_{param_value[1]}"

                            default_params_copy["NAME"] = variant_name

                            self.shader_template_params[template_name].append(
                                default_params_copy
                            )
                    else:
                        default_params_copy = copy.deepcopy(default_params)
                        for key in variant:
                            default_params_copy[key] = variant[key]

                        self.shader_template_params[template_name].append(
                            default_params_copy
                        )