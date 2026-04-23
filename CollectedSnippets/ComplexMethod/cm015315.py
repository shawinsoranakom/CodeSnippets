def test_op_relationship_mapping(self):
        """
        Tests that the mapping of op relationships is complete.
        """
        base_name_to_sets_of_related_ops = get_base_name_to_sets_of_related_ops()
        type_a_related_to_b = \
            get_type_a_related_to_b(base_name_to_sets_of_related_ops)

        # 1. check static quant module mappings
        static_quant_mod_mappings = get_default_static_quant_module_mappings()
        for fp32_type, int8_type in static_quant_mod_mappings.items():
            # skip quants and dequants, for the purposes of Numerical Suite
            types_to_skip = (
                torch.ao.quantization.QuantStub,
                torch.ao.quantization.DeQuantStub,
                nnq.FloatFunctional,
                # the ConvTranspose3d swap is not implemented in FX Graph
                # mode quantization yet
                nn.ConvTranspose3d,
                # the GroupNorm swap is not implemented in FX Graph
                # mode quantization yet
                nn.GroupNorm,
                # nnq.ReLU6 is no longer swapped, because nn.ReLU6 can
                # take quantized inputs
                nn.ReLU6,
            )
            if fp32_type in types_to_skip:
                continue

            # verify relatedness
            in_type_a_related_to_b = \
                (fp32_type, int8_type) in type_a_related_to_b
            self.assertTrue(
                in_type_a_related_to_b,
                f"{fp32_type} and {int8_type} need a relationship mapping")

        # 2. check static quant op mappings
        static_quant_fun_mappings = get_default_float_to_quantized_operator_mappings()
        for fp32_type, int8_type in static_quant_fun_mappings.items():
            # verify relatedness
            in_type_a_related_to_b = \
                (fp32_type, int8_type) in type_a_related_to_b
            self.assertTrue(
                in_type_a_related_to_b,
                f"{fp32_type} and {int8_type} need a relationship mapping")

        # 3. check dynamic quant mappings
        dynamic_quant_mappings = get_default_dynamic_quant_module_mappings()
        for fp32_type, int8_type in dynamic_quant_mappings.items():
            # TODO(future PR): enable correct weight extraction for these
            # and remove from this list.
            types_to_skip = (
                nn.GRUCell,
                nn.GRU,
                nn.LSTMCell,
                nn.RNNCell,
            )
            if fp32_type in types_to_skip:
                continue
            # verify relatedness
            in_type_a_related_to_b = \
                (fp32_type, int8_type) in type_a_related_to_b
            self.assertTrue(
                in_type_a_related_to_b,
                f"{fp32_type} and {int8_type} need a relationship mapping")

        # 4. go through the ops mapped to each QuantizeHandler type, and verify
        # correctness.
        def _op_in_base_sets_of_related_ops(op):
            for ops in base_name_to_sets_of_related_ops.values():
                if op in ops:
                    return True
            return False

        unmatchable_types_map = get_unmatchable_types_map()
        FUNS_UNMATCHABLE = unmatchable_types_map['funs_unmatchable']
        MODS_UNMATCHABLE = unmatchable_types_map['mods_unmatchable']
        METHS_UNMATCHABLE = unmatchable_types_map['meths_unmatchable']

        def _op_is_unmatchable(op):
            return (
                op in FUNS_UNMATCHABLE or
                op in MODS_UNMATCHABLE or
                op in METHS_UNMATCHABLE
            )

        default_quant_patterns = get_all_quant_patterns()
        for pattern, qhandler_cls in default_quant_patterns.items():
            base_op = None
            if isinstance(pattern, tuple):
                base_op = pattern[-1]
            elif isinstance(pattern, str):
                base_op = pattern
            else:
                base_op = pattern

            qhandler_cls_all_ops_quantizeable = [
                qh.CatQuantizeHandler,
                qh.ConvReluQuantizeHandler,
                qh.LinearReLUQuantizeHandler,
                qh.BatchNormQuantizeHandler,
                qh.EmbeddingQuantizeHandler,
                qh.RNNDynamicQuantizeHandler,
            ]

            qhandler_cls_quant_op_same_signature = [
                qh.FixedQParamsOpQuantizeHandler,
                qh.CopyNodeQuantizeHandler,
                qh.GeneralTensorShapeOpQuantizeHandler,
            ]

            if qhandler_cls == qh.BinaryOpQuantizeHandler:
                # these ops do not have quantized equivalents
                ops_to_skip = [
                    torch.bmm,
                    torch.div,
                    torch.sub,
                    operator.truediv,
                    operator.sub
                ]
                if base_op in ops_to_skip:
                    continue
                self.assertTrue(
                    _op_in_base_sets_of_related_ops(base_op),
                    f"{base_op} not in sets of related ops")
            elif qhandler_cls == qh.RNNDynamicQuantizeHandler:
                # TODO(future PR): add support for all classes in
                # RNNDynamicQuantizeHandler
                pass
            elif qhandler_cls == qh.DefaultNodeQuantizeHandler:
                self.assertTrue(
                    _op_in_base_sets_of_related_ops(base_op),
                    f"{base_op} not in sets of related ops")
            elif qhandler_cls in qhandler_cls_quant_op_same_signature:
                # these ops use the same op signature for fp32 and quantized
                # tensors
                self.assertTrue(
                    _op_in_base_sets_of_related_ops(base_op) or
                    _op_is_unmatchable(base_op),
                    f"{base_op} not in sets of related ops or unmatchable")
            elif qhandler_cls in qhandler_cls_all_ops_quantizeable:
                self.assertTrue(
                    _op_in_base_sets_of_related_ops(base_op),
                    f"{base_op} not in sets of related ops")
            else:
                # torch.sum does not have quantized equivalents
                if base_op in [
                        torch.sum,
                        nn.GRUCell,
                        nn.GRU,
                        nn.LSTMCell,
                        nn.RNNCell,
                ]:
                    continue
                if isinstance(base_op, tuple):
                    # skip fusion patterns
                    continue
                # didn't match explicit quantize handler class, we can check if the
                # operator is in the related op set directly
                if not (_op_in_base_sets_of_related_ops(base_op) or _op_is_unmatchable(base_op)):
                    raise AssertionError(
                        f"handling for {qhandler_cls} for op {base_op} not implemented")