def apply_awq_layerwise(dataloader, config, structure, filters=None):
    """Apply AWQ quantization layer-by-layer to a Keras model.

    This function processes the model sequentially, one block at a time:
    1. Captures activation statistics through calibration data forward pass
    2. Uses activation magnitudes to determine weight saliency
    3. Finds optimal per-channel scales via grid search
    4. Quantizes weights with AWQ scaling

    Args:
        dataloader: Calibration data as numpy array.
        config: AWQConfig instance.
        structure: Dict with 'pre_block_layers' and 'sequential_blocks'.
        filters: Optional layer filters.
    """
    num_samples = config.num_samples
    logging.info("Starting AWQ quantization...")

    pre_layers = structure.get("pre_block_layers", [])
    transformer_blocks = structure.get("sequential_blocks", [])

    if not transformer_blocks:
        raise ValueError(
            "No sequential blocks found in the structure to quantize."
        )

    # Process inputs through pre-block layers (e.g., embedding)
    inputs = []
    for batch in dataloader:
        batch = ops.convert_to_tensor(batch, dtype="int32")
        for layer in pre_layers:
            batch = layer(batch)
        inputs.append(batch)

    num_samples = min(num_samples, len(inputs))
    progbar = keras_utils.Progbar(target=len(transformer_blocks))

    for block_idx, block in enumerate(transformer_blocks):
        logging.info(f"Quantizing Block {block_idx}")
        sub_layers_map = find_layers_in_block(block)

        # Apply filters
        final_sub_layers_map = {}
        for name, layer in sub_layers_map.items():
            if not should_quantize_layer(layer, filters):
                continue
            final_sub_layers_map[name] = layer

        sub_layers_map = final_sub_layers_map

        if not sub_layers_map:
            logging.info(
                f"  No quantizable layers found in block {block_idx}. Skipping."
            )
        else:
            logging.info(f"Found layers: {list(sub_layers_map.keys())}")

            # Create AWQ objects for each layer
            awq_objects = {
                name: AWQ(layer, config)
                for name, layer in sub_layers_map.items()
            }

            # Capture activation statistics
            with stream_activations(sub_layers_map, awq_objects):
                for sample_idx in range(num_samples):
                    current_input = inputs[sample_idx]
                    if len(current_input.shape) == 2:
                        current_input = ops.expand_dims(current_input, axis=0)
                    _ = block(current_input)

            # Quantize each layer
            for name, awq_object in awq_objects.items():
                logging.info(f"Quantizing {name}...")
                awq_object.quantize_layer()
                awq_object.free()

            del awq_objects

        # Generate inputs for next block
        if block_idx < len(transformer_blocks) - 1:
            logging.info(f"Generating inputs for block {block_idx + 1}...")
            next_block_inputs = []
            for sample_idx in range(num_samples):
                current_input = inputs[sample_idx]
                if len(current_input.shape) == 2:
                    current_input = ops.expand_dims(current_input, axis=0)
                output = block(current_input)[0]
                next_block_inputs.append(output)
            inputs = next_block_inputs

        progbar.update(current=block_idx + 1)

    logging.info("AWQ quantization complete.")