def test_op_io_dtype_coverage(self):
        """
        Tests that all the ops quantization cares about have input and output
        dtypes defined.
        """
        base_name_to_sets_of_related_ops = get_base_name_to_sets_of_related_ops()
        type_a_related_to_b = \
            get_type_a_related_to_b(base_name_to_sets_of_related_ops)

        # TODO(future PR): clean this up
        node_type_to_io_type_map = get_node_type_to_io_type_map()
        FUNS_IO_TYPE_FP32 = node_type_to_io_type_map['funs_io_type_fp32']
        FUNS_IO_TYPE_INT8 = node_type_to_io_type_map['funs_io_type_int8']
        FUNS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map['funs_io_type_fp32_or_int8']
        MODS_IO_TYPE_FP32 = node_type_to_io_type_map['mods_io_type_fp32']
        MODS_IO_TYPE_INT8 = node_type_to_io_type_map['mods_io_type_int8']
        MODS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map['mods_io_type_fp32_or_int8']
        METHS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map['meths_io_type_fp32_or_int8']

        unmatchable_types_map = get_unmatchable_types_map()
        FUNS_UNMATCHABLE = unmatchable_types_map['funs_unmatchable']
        MODS_UNMATCHABLE = unmatchable_types_map['mods_unmatchable']
        METHS_UNMATCHABLE = unmatchable_types_map['meths_unmatchable']

        # 1. check static quant module mappings
        static_quant_mod_mappings = get_default_static_quant_module_mappings()
        for fp32_type, int8_type in static_quant_mod_mappings.items():
            types_to_skip = (
                torch.ao.quantization.QuantStub,
                torch.ao.quantization.DeQuantStub,
                nnq.FloatFunctional,
                # TODO(future PR): look into whether shadowing embeddings
                # makes sense
                nn.Embedding,
                nn.EmbeddingBag,
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
            self.assertTrue(
                fp32_type in MODS_IO_TYPE_FP32,
                f"missing IO type handling for f{fp32_type}")
            self.assertTrue(
                int8_type in MODS_IO_TYPE_INT8,
                f"missing IO type handling for f{int8_type}")

        # 2. check static quant op mappings
        static_quant_fun_mappings = get_default_float_to_quantized_operator_mappings()
        for fp32_type, int8_type in static_quant_fun_mappings.items():
            self.assertTrue(
                fp32_type in FUNS_IO_TYPE_FP32,
                f"missing IO type handling for f{fp32_type}")
            self.assertTrue(
                int8_type in FUNS_IO_TYPE_INT8,
                f"missing IO type handling for f{int8_type}")

        # 3. check dynamic quant mappings
        dynamic_quant_mappings = get_default_dynamic_quant_module_mappings()
        for fp32_type1, fp32_type2 in dynamic_quant_mappings.items():
            # TODO(future PR): verify correct I/O for these and remove from
            # this list.
            types_to_skip = (
                nn.GRUCell,
                nn.GRU,
                nn.LSTMCell,
                nn.RNNCell,
                # TODO(future PR): look into whether shadowing embeddings
                # makes sense
                nn.Embedding,
                nn.EmbeddingBag,
            )
            if fp32_type1 in types_to_skip:
                continue
            self.assertTrue(
                fp32_type1 in MODS_IO_TYPE_FP32,
                f"missing IO type handling for f{fp32_type1}")
            self.assertTrue(
                fp32_type2 in MODS_IO_TYPE_FP32,
                f"missing IO type handling for f{fp32_type2}")

        # 4. go through the ops mapped to each QuantizeHandler type, and verify
        # correctness.
        default_quant_patterns = get_all_quant_patterns()
        for pattern, qhandler_cls in default_quant_patterns.items():
            base_op = None
            if isinstance(pattern, tuple):
                base_op = pattern[-1]
            elif isinstance(pattern, str):
                base_op = pattern
            else:
                base_op = pattern

            if (
                qhandler_cls in (
                    qh.BinaryOpQuantizeHandler,
                    qh.RNNDynamicQuantizeHandler,
                )
            ):
                # TODO(future PR): implement shadowing for binary ops
                # TODO(future PR): implement shadowing for RNN ops
                continue
            elif qhandler_cls == qh.CatQuantizeHandler:
                self.assertTrue(
                    base_op in FUNS_IO_TYPE_FP32_OR_INT8,
                    f"missing IO type handling for {base_op}")
            elif (
                qhandler_cls in (
                    qh.ConvReluQuantizeHandler,
                    qh.LinearReLUQuantizeHandler,
                    qh.BatchNormQuantizeHandler,
                    qh.DefaultNodeQuantizeHandler,
                )
            ):
                self.assertTrue(
                    (base_op in FUNS_IO_TYPE_FP32) or (base_op in MODS_IO_TYPE_FP32),
                    f"missing IO type handling for {base_op}")
            elif (
                qhandler_cls in (
                    qh.FixedQParamsOpQuantizeHandler,
                    qh.CopyNodeQuantizeHandler,
                    qh.GeneralTensorShapeOpQuantizeHandler,
                )
            ):
                if (
                    base_op in FUNS_UNMATCHABLE or
                    base_op in MODS_UNMATCHABLE or
                    base_op in METHS_UNMATCHABLE
                ):
                    continue

                self.assertTrue(
                    (base_op in FUNS_IO_TYPE_FP32_OR_INT8) or
                    (base_op in MODS_IO_TYPE_FP32_OR_INT8) or
                    (base_op in METHS_IO_TYPE_FP32_OR_INT8) or
                    # Softmax has a different signature for the quantized
                    # version, so it does not fit into the cases above.
                    (base_op is torch.nn.Softmax),
                    f"missing IO type handling for {base_op}")
            elif qhandler_cls == qh.EmbeddingQuantizeHandler:
                # embedding shadowing is not implemented, for now
                continue
            else:
                if (
                    base_op in FUNS_UNMATCHABLE or
                    base_op in MODS_UNMATCHABLE or
                    base_op in METHS_UNMATCHABLE
                ):
                    continue
                if qhandler_cls(None, {}).is_general_tensor_value_op():
                    self.assertTrue(
                        (base_op in FUNS_IO_TYPE_FP32_OR_INT8) or
                        (base_op in MODS_IO_TYPE_FP32_OR_INT8) or
                        (base_op in METHS_IO_TYPE_FP32_OR_INT8),
                        f"missing IO type handling for {base_op} using {qhandler_cls}")
                else:
                    self.assertTrue(
                        (base_op in FUNS_IO_TYPE_FP32_OR_INT8) or
                        (base_op in MODS_IO_TYPE_FP32_OR_INT8) or
                        (base_op in METHS_IO_TYPE_FP32_OR_INT8) or
                        (base_op in FUNS_IO_TYPE_FP32) or
                        (base_op in MODS_IO_TYPE_FP32) or
                        f"missing IO type handling for {base_op} using {qhandler_cls}")