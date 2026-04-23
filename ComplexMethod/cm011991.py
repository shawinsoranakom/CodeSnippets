def unwrap_storage_for_input(cls, x: IRNode) -> IRNode:
        if isinstance(x, TensorBox):
            x = x.data
        if isinstance(x, StorageBox):
            x = x.data
        if isinstance(x, BaseView) and not isinstance(x, ReinterpretView):
            x = ExternKernel.realize_input(x)
        if isinstance(x, TensorBox):
            # when converting to ReinterpretView fails in the
            # realize_input call above, the result will be wrapped
            # into TensorBox / StorageBox pair as a result of the
            # cls.copy_input call; so we should unwrap recursively
            return cls.unwrap_storage_for_input(x)
        if isinstance(x, TorchBindObject):
            return x
        assert isinstance(x, (Buffer, ReinterpretView)), type(x)
        return x