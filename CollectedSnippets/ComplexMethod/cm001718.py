def _get_component_class_from_processor(cls, attribute, use_fast: bool = True):
        """
        Get the component class for a given attribute from the processor's Auto mappings.

        This extracts the model type from the test file name and uses that to look up
        the config class, which is then used to find the appropriate component class.
        """
        import inspect
        import re

        from transformers.models.auto.configuration_auto import (
            CONFIG_MAPPING_NAMES,
            SPECIAL_MODEL_TYPE_TO_MODULE_NAME,
        )

        # Get the component class from the appropriate Auto mapping
        if attribute in MODALITY_TO_AUTOPROCESSOR_MAPPING:
            mapping_name = attribute
        elif "tokenizer" in attribute:
            mapping_name = "tokenizer"
        else:
            raise ValueError(
                f"Unknown attribute type: '{attribute}'. "
                f"Please override _setup_{attribute}() in your test class to provide custom setup."
            )

        # Extract model_type from the test file name
        # Test files are named like test_processing_align.py or test_processor_align.py
        test_file = inspect.getfile(cls)
        match = re.search(r"test_process(?:ing|or)_(\w+)\.py$", test_file)
        if not match:
            raise ValueError(
                f"Could not extract model type from test file name: {test_file}. "
                f"Please override _setup_{attribute}() in your test class."
            )

        model_type = match.group(1)

        if model_type not in CONFIG_MAPPING_NAMES:
            # check if the model type is a special model type
            for special_model_type, special_module_name in SPECIAL_MODEL_TYPE_TO_MODULE_NAME.items():
                if model_type != special_module_name or special_model_type not in CONFIG_MAPPING_NAMES:
                    continue

                component_class = cls.resolve_model_type_to_attribute(special_model_type, mapping_name)
                if component_class is not None:
                    break
        else:
            component_class = cls.resolve_model_type_to_attribute(model_type, mapping_name)

        if component_class is None:
            raise ValueError(
                f"Could not find {mapping_name} class for model {match.group(1)}. "
                f"Please override _setup_{attribute}() in your test class."
            )

        # Handle tuple case (some mappings return tuples of classes)
        if isinstance(component_class, tuple):
            if use_fast:
                component_class = component_class[-1] if component_class[-1] is not None else component_class[0]
            else:
                component_class = component_class[0] if component_class[0] is not None else component_class[1]
        elif isinstance(component_class, dict):
            if not use_fast:
                component_class = component_class["pil"]
            else:
                component_class = (
                    component_class["torchvision"] if "torchvision" in component_class else component_class["pil"]
                )
        return component_class