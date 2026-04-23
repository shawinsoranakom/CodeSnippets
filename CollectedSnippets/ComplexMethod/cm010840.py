def flatten_subclass(
        t: FxValue,
        desc: AOTDescriptor,
        *,
        out: tuple[list[FxValue], list[AOTDescriptor]],
    ) -> None:
        # unwrap a subclass into plain tensors and their size/stride if "append_symint"
        # is True
        if not is_traceable_wrapper_subclass(t):
            out[0].append(_maybe_fakeify_opaque(t))
            out[1].append(desc)
            return

        attrs, _ = t.__tensor_flatten__()

        SubclassGetAttr: Callable[[AOTInput | AOTOutput, str], AOTDescriptor]
        SubclassSize: Callable[[AOTInput | AOTOutput, int], AOTDescriptor]
        SubclassStride: Callable[[AOTInput | AOTOutput, int], AOTDescriptor]
        if isinstance(desc, AOTInput):
            SubclassGetAttr = SubclassGetAttrAOTInput  # type: ignore[bad-assignment]
            SubclassSize = SubclassSizeAOTInput  # type: ignore[bad-assignment]
            SubclassStride = SubclassStrideAOTInput  # type: ignore[bad-assignment]
        else:
            SubclassGetAttr = SubclassGetAttrAOTOutput  # type: ignore[bad-assignment]
            SubclassSize = SubclassSizeAOTOutput  # type: ignore[bad-assignment]
            SubclassStride = SubclassStrideAOTOutput  # type: ignore[bad-assignment]

        for attr in attrs:
            inner_value = getattr(t, attr)
            n_desc: Any = SubclassGetAttr(desc, attr)
            flatten_subclass(inner_value, n_desc, out=out)

        if append_symints:
            sizes = enumerate_filter_symints(t.size())
            strides = enumerate_filter_symints(t.stride())
            out[0].extend(s for _, s in sizes)
            out[0].extend(s for _, s in strides)
            out[1].extend(SubclassSize(desc, i) for i, _ in sizes)
            out[1].extend(SubclassStride(desc, i) for i, _ in strides)