def convert(
        self,
        layer_name: str,
        model=None,
        config=None,
        hf_quantizer=None,
        loading_info: LoadStateDictInfo | None = None,
    ):
        # Collect the tensors here - we use a new dictionary to avoid keeping them in memory in the internal
        # attribute during the whole process
        collected_tensors = self.materialize_tensors()

        for op in self.operations:
            with log_conversion_errors(layer_name, loading_info, (len(collected_tensors), layer_name), op):
                collected_tensors = op.convert(
                    collected_tensors,
                    source_patterns=self.source_patterns,
                    target_patterns=self.target_patterns,
                    # Additional kwargs, usually not used
                    full_layer_name=layer_name,
                    model=model,
                    config=config,
                    missing_keys=loading_info.missing_keys if loading_info else None,
                )

        # Tensors are returned from ops with the target patterns, we need to expand them to full name.
        # This means we need to grab the prefix and suffix to add to every target key
        full_name = layer_name
        if ".*." in layer_name:
            full_name = layer_name.replace(".*.", ".0.")

        try:
            prefix, _, suffix = next(full_name.partition(k) for k in collected_tensors.keys() if k in full_name)
            # Rename the tensors
            collected_tensors = {prefix + k + suffix: v for k, v in collected_tensors.items()}
        # some quantizers need to already rename in `convert` as they cannot only rely on prefix and suffix
        except StopIteration:
            pass

        if hf_quantizer is not None and self.quantization_operation is not None:
            with log_conversion_errors(
                layer_name, loading_info, (len(collected_tensors), layer_name), self.quantization_operation
            ):
                collected_tensors = self.quantization_operation.convert(
                    collected_tensors,
                    source_patterns=self.source_patterns,
                    target_patterns=self.target_patterns,
                    full_layer_name=layer_name,
                    config=config,
                    model=model,
                    missing_keys=loading_info.missing_keys if loading_info else None,
                )
        return collected_tensors