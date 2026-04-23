def testQuantizationBuilderAddsQuantOverride(self):
    graph = ops.Graph()
    with graph.as_default():
      self._buildGraph()

      quant_overrides_proto = quant_overrides_pb2.QuantOverrides()
      quant_config = quant_overrides_proto.quant_configs.add()
      quant_config.op_name = 'test_graph/add_ab'
      quant_config.quant_op_name = 'act_quant'
      quant_config.fixed_range = True
      quant_config.min = 0
      quant_config.max = 6
      quant_config.delay = 100

      graph_rewriter_proto = graph_rewriter_pb2.GraphRewriter()
      graph_rewriter_proto.quantization.delay = 10
      graph_rewriter_proto.quantization.weight_bits = 8
      graph_rewriter_proto.quantization.activation_bits = 8

      graph_rewrite_fn = graph_rewriter_builder.build(
          graph_rewriter_proto,
          quant_overrides_config=quant_overrides_proto,
          is_training=True)
      graph_rewrite_fn()

      act_quant_found = False
      quant_delay_found = False
      for op in graph.get_operations():
        if (quant_config.quant_op_name in op.name and
            op.type == 'FakeQuantWithMinMaxArgs'):
          act_quant_found = True
          min_val = op.get_attr('min')
          max_val = op.get_attr('max')
          self.assertEqual(min_val, quant_config.min)
          self.assertEqual(max_val, quant_config.max)
        if ('activate_quant' in op.name and
            quant_config.quant_op_name in op.name and op.type == 'Const'):
          tensor = op.get_attr('value')
          if tensor.int64_val[0] == quant_config.delay:
            quant_delay_found = True

      self.assertTrue(act_quant_found)
      self.assertTrue(quant_delay_found)