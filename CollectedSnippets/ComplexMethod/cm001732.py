def _verify_and_infer_model_attributes(cls):
        """
        Verifies that the required tester attributes are set correctly, and infers unset tester attributes.
        Intentionally nitpicks the tester class attributes, to prevent human errors.
        """
        # `base_model_class` is mandatory, and it must be a valid model class.
        base_model_class = getattr(cls, "base_model_class")
        if base_model_class is None or "PreTrainedModel" not in str(base_model_class.__mro__):
            raise ValueError(
                f"You have inherited from `CausalLMModelTester` but did not set the `base_model_class` "
                f"attribute to a valid model class. (It's set to `{base_model_class}`)"
            )

        # Infers other model classes from the base class name and available public classes, if the corresponding
        # attributes are not set explicitly. If they are set, they must be set to a valid class (config or model).
        model_name = base_model_class.__name__.replace("Model", "")
        base_class_module = ".".join(base_model_class.__module__.split(".")[:-1])
        for tester_attribute_name, model_class_termination in _COMMON_MODEL_NAMES_MAP.items():
            if getattr(cls, tester_attribute_name) is None:
                try:
                    model_class = getattribute_from_module(base_class_module, model_name + model_class_termination)
                    setattr(cls, tester_attribute_name, model_class)
                except ValueError:
                    pass
            else:
                if tester_attribute_name == "config_class":
                    if "PreTrainedConfig" not in str(getattr(cls, tester_attribute_name).__mro__):
                        raise ValueError(
                            f"You have inherited from `CausalLMModelTester` but did not set the "
                            f"`{tester_attribute_name}` attribute to a valid config class. (It's set to "
                            f"`{getattr(cls, tester_attribute_name)}`). If the config class follows a standard "
                            f"naming convention, you should unset `{tester_attribute_name}`."
                        )
                else:
                    if "PreTrainedModel" not in str(getattr(cls, tester_attribute_name).__mro__):
                        raise ValueError(
                            f"You have inherited from `CausalLMModelTester` but did not set the "
                            f"`{tester_attribute_name}` attribute to a valid model class. (It's set to "
                            f"`{getattr(cls, tester_attribute_name)}`). If the model class follows a standard "
                            f"naming convention, you should unset `{tester_attribute_name}`."
                        )

        # After inferring, if we don't have the basic classes set, we raise an error.
        for required_attribute in cls._required_attributes:
            if getattr(cls, required_attribute) is None:
                raise ValueError(
                    f"You have inherited from `CausalLMModelTester` but did not set the `{required_attribute}` "
                    "attribute. It can't be automatically inferred either -- this means it is not following a "
                    "standard naming convention. If this is intentional, please set the attribute explicitly."
                )

        # To prevent issues with typos, no other attributes can be set to a model class
        for instance_attribute_name, instance_attribute in cls.__dict__.items():
            if (
                (
                    instance_attribute_name not in _COMMON_MODEL_NAMES_MAP
                    and instance_attribute_name != "base_model_class"
                )
                and isinstance(instance_attribute, type)
                and "PreTrainedModel" in str(instance_attribute.__mro__)
            ):
                raise ValueError(
                    f"You have inherited from `CausalLMModelTester` but set an unexpected attribute to a model class "
                    f"(`{instance_attribute_name}` is set to `{instance_attribute}`). "
                    f"Only the following attributes can be set to model classes: {_COMMON_MODEL_NAMES_MAP.keys()}."
                )