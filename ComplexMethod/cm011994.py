def realize_into(cls, src: IRNode, dst: IRNode) -> IRNode:
        # Attempt to turn this into a ReinterpretView rather than assert.
        # This has concessions around layout, as as_storage_and_layout
        # can cause us to go from flexible to fixed layout.
        if not isinstance(dst, ReinterpretView):
            if is_storage_and_layout(dst):
                storage, layout = as_storage_and_layout(dst)
                dst = ReinterpretView(data=storage, layout=layout)
        assert isinstance(dst, ReinterpretView), type(dst)
        if isinstance(src, TensorBox):
            # unwrap a TensorBox
            return cls.realize_into(src.data, dst)

        if isinstance(src, StorageBox):
            src.realize()
            # ExternKernelAlloc has specific requirements for output layout, should create a copy
            assert hasattr(src.data, "layout")
            if cls.can_realize_into_without_copy(src, dst):
                # pyrefly: ignore [missing-attribute]
                src.data.layout = NonOwningLayout(dst)
                return src.data
        # introduce a copy
        pw = Pointwise.create(
            device=src.get_device(),
            dtype=src.get_dtype(),
            inner_fn=src.make_loader(),
            ranges=[
                V.graph.sizevars.check_equals_and_simplify(a, b)
                for a, b in zip(src.get_size(), dst.get_size())
            ],
        )
        return cls.realize_into(pw, dst)