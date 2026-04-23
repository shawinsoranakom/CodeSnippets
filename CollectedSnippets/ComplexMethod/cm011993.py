def can_realize_into_without_copy(
        cls, src: IRNode, dst: IRNode | None = None
    ) -> bool:
        if isinstance(src, TensorBox):
            # unwrap a TensorBox
            return cls.can_realize_into_without_copy(src.data, dst)

        assert isinstance(src, (BaseView, StorageBox)), type(src)
        if isinstance(src.data, MultiTemplateBuffer):
            if (
                not isinstance(src.data.layout, FixedLayout)
                or not src.data.output_plannable
            ):
                return False

            # we call can_realize_into_without_copy in cat lowering before we've decided
            # on output format, optimistically assume layout matches
            if dst is None:
                return True

            # otherwise, check equality of layouts
            if len(src.get_stride()) != len(dst.get_stride()):
                return False

            return all(
                V.graph.sizevars.statically_known_equals(s1, s2)
                for s1, s2 in zip(src.get_stride(), dst.get_stride())
            )

        return (
            hasattr(src.data, "layout")
            and isinstance(src.data.layout, FlexibleLayout)
            and not isinstance(src.data, ExternKernelAlloc)
        )