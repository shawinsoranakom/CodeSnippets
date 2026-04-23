def _create_output_spec_with_new_tensor_meta(
        self,
        op: OpOverload,
        output_specs: OutputSpecType,
        output_tensor_meta: TensorMeta | Sequence[TensorMeta | None] | None,
    ) -> OutputSpecType:
        """
        Wrap the output_specs with the tensor metadata from the output.
        """

        if isinstance(output_specs, DTensorSpec):
            if not isinstance(output_tensor_meta, TensorMeta):
                # Either error due to ShardingPropagator or due to incorrect OutputSpec
                if not isinstance(output_tensor_meta, (tuple, list)):
                    raise ValueError(
                        "ShardingPropagator error: output does not have an associated "
                        "TensorMeta"
                    )
                raise ValueError(
                    f"For the op {op.name()}, `output_specs` has 1 output which does "
                    "not equal the "
                    f"number of op outputs: {len(output_tensor_meta)}."
                )
            return output_specs.shallow_copy_with_tensor_meta(output_tensor_meta)
        elif isinstance(output_specs, (tuple, list)):
            new_specs: list[DTensorSpec | None] = []
            if not isinstance(output_tensor_meta, (tuple, list)) or len(
                output_specs
            ) != len(output_tensor_meta):
                raise ValueError(
                    f"For the op {op.name()}, `output_specs` has {len(output_specs)} "
                    "outputs which does not equal the "
                    f"number of op outputs {_length(output_tensor_meta)}."
                )

            # pyrefly: ignore [bad-argument-type]
            for i, spec in enumerate(output_specs):
                if isinstance(spec, DTensorSpec):
                    output_tensor_meta_i = output_tensor_meta[i]
                    if not isinstance(output_tensor_meta_i, TensorMeta):
                        # Some ops (e.g. convolution_backward, native_layer_norm_backward,
                        # _fused_rms_norm_backward) have an output_mask parameter that
                        # controls which outputs are computed. When output_mask[i] is
                        # False, the output at position i is None and has no TensorMeta.
                        if output_tensor_meta_i is None:
                            new_specs.append(None)
                            continue
                        else:
                            raise ValueError(
                                f"ShardingPropagator error: output {i} of {op.name()} "
                                "does not have an associated TensorMeta"
                            )

                    new_specs.append(
                        spec.shallow_copy_with_tensor_meta(output_tensor_meta_i)
                    )
                else:
                    new_specs.append(spec)

            return tuple(new_specs)
        else:
            if output_specs is not None:
                raise AssertionError
            return output_specs