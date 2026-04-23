def validate_layer_type(self):
        """
        Validate layers_block_type list.
        """
        if not isinstance(self.layer_types, list):
            raise ValueError(f"`layers_block_type` must be a list of strings. Got type: {type(self.layer_types)}")

        valid_types = {"mamba", "attention", "moe", "mlp"}
        if not all(block_type in valid_types for block_type in self.layer_types):
            invalid = set(self.layer_types) - valid_types
            raise ValueError(f"`layers_block_type` contains invalid types: {invalid}. Must be one of: {valid_types}")

        if self.num_nextn_predict_layers > 0:
            if self.mtp_layers_block_type is None:
                raise ValueError(
                    "mtp_layers_block_type is required when num_nextn_predict_layers > 0. "
                    "Please provide an explicit list of layer types for MTP layers. "
                    "Example: mtp_layers_block_type=['attention', 'moe']"
                )

            if not isinstance(self.mtp_layers_block_type, list):
                raise ValueError(
                    f"`mtp_layers_block_type` must be a list of strings. Got type: {type(self.mtp_layers_block_type)}"
                )

            if not all(block_type in valid_types for block_type in self.mtp_layers_block_type):
                invalid = set(self.mtp_layers_block_type) - valid_types
                raise ValueError(
                    f"`mtp_layers_block_type` contains invalid types: {invalid}. Must be one of: {valid_types}"
                )