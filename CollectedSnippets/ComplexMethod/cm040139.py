def export(self, filepath):
        """Exports the Keras model to a TFLite file.

        Args:
            filepath: Output path for the exported model

        Returns:
            Path to exported model
        """
        # 1. Resolve / infer input signature
        if self.input_signature is None:
            # Use the standard get_input_signature which handles all model types
            # and preserves nested structures (dicts, lists, etc.)
            self.input_signature = get_input_signature(self.model)

        # 2. Determine input structure and create adapter if needed
        # There are 3 cases:
        # Case 1: Single input (not nested)
        # Case 2: Flat list of inputs (list where flattened == original)
        # Case 3: Nested structure (dicts, nested lists, etc.)

        # Special handling for Functional models: get_input_signature wraps
        # the structure in a list, so unwrap it for analysis
        input_struct = self.input_signature
        if (
            isinstance(self.input_signature, list)
            and len(self.input_signature) == 1
        ):
            input_struct = self.input_signature[0]

        if not tree.is_nested(input_struct):
            # Case 1: Single input - use as-is
            model_to_convert = self.model
            signature_for_conversion = self.input_signature
        elif isinstance(input_struct, list) and len(input_struct) == len(
            tree.flatten(input_struct)
        ):
            # Case 2: Flat list of inputs - use as-is
            model_to_convert = self.model
            signature_for_conversion = self.input_signature
        else:
            # Case 3: Nested structure (dict, nested lists, etc.)
            # Create adapter model that converts flat list to nested structure
            adapted_model = self._create_nested_inputs_adapter(input_struct)

            # Flatten signature for TFLite conversion
            signature_for_conversion = tree.flatten(input_struct)

            # Use adapted model and flat list signature for conversion
            model_to_convert = adapted_model

        # Store original model reference for later use
        original_model = self.model

        # Temporarily replace self.model with the model to convert
        self.model = model_to_convert

        try:
            # Convert the model to TFLite.
            tflite_model = self._convert_to_tflite(signature_for_conversion)
        finally:
            # Restore original model
            self.model = original_model

        # Save the TFLite model to the specified file path.
        if not filepath.endswith(".tflite"):
            raise ValueError(
                f"The LiteRT export requires the filepath to end with "
                f"'.tflite'. Got: {filepath}"
            )

        with open(filepath, "wb") as f:
            f.write(tflite_model)

        return filepath