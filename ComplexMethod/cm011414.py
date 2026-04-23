def _propagate_tensor_meta_non_cached(
        self, op_schema: OpSchema
    ) -> TensorMeta | Sequence[TensorMeta | None] | None:
        """
        Propagate the tensor metadata, it could either return a TensorMeta
        or a list/tuple of TensorMetas
        """
        if op_schema.op == aten.equal.default:
            # data dependent ops can't be used for fake propagation
            return None

        # NOTE: We must call the tracing in fake tensor mode so that it avoids
        # materializing memory.
        # NOTE: Use _fake_mode_lock to serialize access when running in
        # multi-threaded tests (lock must be set to threading.Lock()).
        # This is a nullcontext by default.
        with ShardingPropagator._fake_mode_lock:
            fake_mode = detect_fake_mode() or FakeTensorMode()
            with fake_mode:
                fake_args = op_schema.gen_fake_args()
                fake_kwargs = op_schema.gen_fake_kwargs()
                fake_out = op_schema.op(*fake_args, **fake_kwargs)

        if isinstance(fake_out, torch.Tensor):
            return TensorMeta(
                shape=fake_out.shape, stride=fake_out.stride(), dtype=fake_out.dtype
            )

        elif isinstance(fake_out, (tuple, list)):
            tensor_meta_list: list[TensorMeta | None] = []
            for fake_out_item in fake_out:
                if isinstance(fake_out_item, torch.Tensor):
                    tensor_meta_list.append(
                        TensorMeta(
                            shape=fake_out_item.shape,
                            stride=fake_out_item.stride(),
                            dtype=fake_out_item.dtype,
                        )
                    )
                else:
                    tensor_meta_list.append(None)
            return (
                tuple(tensor_meta_list)
                if isinstance(fake_out, tuple)
                else tensor_meta_list
            )
        else:
            # if fake is not a tensor or tuple of tensor, return as none
            return None