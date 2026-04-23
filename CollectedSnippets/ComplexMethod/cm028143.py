def graph_rewrite_fn():
    """Function to quantize weights and activation of the default graph."""
    if (graph_rewriter_config.quantization.weight_bits != 8 or
        graph_rewriter_config.quantization.activation_bits != 8):
      raise ValueError('Only 8bit quantization is supported')

    graph = tf.get_default_graph()

    # Insert custom quant ops.
    if quant_overrides_config is not None:
      input_to_ops_map = input_to_ops.InputToOps(graph)
      for q in quant_overrides_config.quant_configs:
        producer = graph.get_operation_by_name(q.op_name)
        if producer is None:
          raise ValueError('Op name does not exist in graph.')
        context = _get_context_from_op(producer)
        consumers = input_to_ops_map.ConsumerOperations(producer)
        if q.fixed_range:
          _insert_fixed_quant_op(
              context,
              q.quant_op_name,
              producer,
              consumers,
              init_min=q.min,
              init_max=q.max,
              quant_delay=q.delay if is_training else 0)
        else:
          raise ValueError('Learned ranges are not yet supported.')

    # Quantize the graph by inserting quantize ops for weights and activations
    if is_training:
      contrib_quantize.experimental_create_training_graph(
          input_graph=graph,
          quant_delay=graph_rewriter_config.quantization.delay,
          freeze_bn_delay=graph_rewriter_config.quantization.delay)
    else:
      contrib_quantize.experimental_create_eval_graph(
          input_graph=graph,
          quant_delay=graph_rewriter_config.quantization.delay
          if not is_export else 0)

    contrib_layers.summarize_collection('quant_vars')