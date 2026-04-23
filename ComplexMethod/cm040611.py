def apply_gptq_layerwise(dataloader, config, structure, filters=None):
    """Applies GPTQ quantization layer-by-layer to a Keras model.

    This function uses the provided `structure` to identify pre-quantization
    layers and sequential blocks.

    The core logic operates as follows:

    1.  It processes the model sequentially, one block at a time. For each
        block, it uses temporary hooks to capture the input activations of
        each target layer during a forward pass with the calibration data.
    2.  These captured activations are used to compute the Hessian matrix for
        each layer's weights.
    3.  The GPTQ algorithm is then applied to each layer to find the optimal
        quantized weights that minimize the error introduced.
    4.  The output activations from the current block are then used as the
        input for the next block, ensuring that quantization errors are
        accounted for throughout the model.

    Args:
        dataloader: An iterable providing calibration data.
        config: A GPTQConfiguration object.
        structure: A dictionary with keys "pre_block_layers" and
            "sequential_blocks".
        filters: Optional filters to exclude layers from quantization.

    Raises:
        ValueError: If the function cannot automatically find an embedding
            layer or any transformer-like blocks to quantize within the model.
    """

    num_samples = config.num_samples

    logging.info("Starting model quantization...")

    pre_layers = structure.get("pre_block_layers", [])
    transformer_blocks = structure.get("sequential_blocks", [])

    if not transformer_blocks:
        raise ValueError(
            "No sequential blocks found in the provided structure to quantize."
        )

    # Initial inputs are the outputs of the pre-block layers
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

        # Filter out layers that are not quantized with GPTQ
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
            gptq_objects = {
                name: GPTQ(layer, config)
                for name, layer in sub_layers_map.items()
            }

            with stream_hessians(sub_layers_map, gptq_objects):
                for sample_idx in range(num_samples):
                    current_input = inputs[sample_idx]
                    if len(current_input.shape) == 2:
                        current_input = ops.expand_dims(current_input, axis=0)
                    _ = block(current_input)

            for name, gptq_object in gptq_objects.items():
                logging.info(f"Quantizing {name}...")
                gptq_object.quantize_and_correct_layer()
                gptq_object.free()

            del gptq_objects

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

    logging.info("Quantization process complete.")