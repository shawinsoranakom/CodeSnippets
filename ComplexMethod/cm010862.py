def process_runtime_tangent(
        x: Any,
        meta: PlainTensorMeta | SubclassCreationMeta,
        tangent_idx: int | None = None,
        tangent_desc: Any | None = None,
        compile_id_str: str | None = None,
        tangent_stack_trace: str | None = None,
    ) -> tuple[Any, list[Any]]:
        if not isinstance(x, torch.Tensor):
            return x, [x]

        if isinstance(x, FakeTensor):
            if not meta.memory_format:
                raise AssertionError(
                    "meta.memory_format must not be None for FakeTensor"
                )
            x = coerce_to_expected_memory_format(x, meta.memory_format)
            return x, [x]

        expected_type: type | None = torch.Tensor
        expected_meta = None
        if isinstance(meta, SubclassCreationMeta):
            expected_type = meta.original_subclass_type
            expected_meta = meta.meta

        runtime_type = type(x)
        # When we're inside compiled autograd's AOTDispatcher step,
        # regular Tensors look like FunctionalTensors.
        # Tensor subclasses still look like Tensor subclasses though.
        if isinstance(x, torch._subclasses.functional_tensor.FunctionalTensor):
            runtime_type = torch.Tensor

        runtime_meta = None
        runtime_subclass_keys: Sequence[str] = []

        if is_traceable_wrapper_subclass(x):
            runtime_subclass_keys, runtime_meta = x.__tensor_flatten__()

        def maybe_coerce(x: torch.Tensor) -> torch.Tensor | None:
            same_type: bool = expected_type == runtime_type
            same_meta: bool = expected_meta == runtime_meta

            if same_type and same_meta:
                return x

            if not hasattr(x, "__coerce_same_metadata_as_tangent__"):
                return None

            if same_type:
                # Backward Compatibility, as some Subclass impls can have original 1-arg function.
                return x.__coerce_same_metadata_as_tangent__(expected_meta)

            return x.__coerce_same_metadata_as_tangent__(expected_meta, expected_type)

        # Coerce to expected type and metadata
        orig_x = x
        x = maybe_coerce(x)
        if x is None:
            raise AOTDispatchAutograd._raise_tangent_metadata_error(
                expected_type,
                expected_meta,
                runtime_type,
                runtime_meta,
                orig_x,
                tangent_idx,
                tangent_desc,
                compile_id_str,
                tangent_stack_trace,
            )

        # Coerce to expected memory format
        if not meta.memory_format:
            raise AssertionError("meta.memory_format must not be None")
        x = coerce_to_expected_memory_format(x, meta.memory_format)

        if not is_traceable_wrapper_subclass(x):
            return x, [x]

        if not isinstance(meta, SubclassCreationMeta):
            raise AssertionError(f"expected SubclassCreationMeta, got {type(meta)}")
        if orig_x is not x:
            runtime_subclass_keys = x.__tensor_flatten__()[0]

        if len(meta.attrs) != len(runtime_subclass_keys):
            raise AssertionError(
                f"expected len(meta.attrs) == len(runtime_subclass_keys), "
                f"got {len(meta.attrs)} != {len(runtime_subclass_keys)}"
            )
        leaves = []
        for attr, attr_meta in meta.attrs.items():
            if isinstance(attr_meta, OpaqueMeta):
                # Opaques aren't differentiable but occupy a flat arg slot.
                leaves.append(getattr(x, attr))
                continue
            elem = getattr(x, attr)
            new_elem, elem_leaves = AOTDispatchAutograd.process_runtime_tangent(
                elem, attr_meta
            )
            if new_elem is not elem:
                setattr(x, attr, new_elem)
            leaves.extend(elem_leaves)

        return x, leaves