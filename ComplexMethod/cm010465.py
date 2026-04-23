def __torch_dispatch__(  # type: ignore[override]
        self,
        func: OpOverload,
        types: Sequence[type],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if _has_unrecognized_tensor_types(types):
            return NotImplemented

        if kwargs is None:
            kwargs = {}
        # FunctionalTensor needs to plumb all metadata requests to the inner tensor.
        # In theory we don't have to do this - but if we want to service metadata requests here,
        # we need to carefully make sure all metadata is accurate (including metadata mutations)
        if func in FunctionalTensor.metadata_fns:
            # All metadata accesses should be plumbed to the inner tensor, that way we don't have to worry
            # about the problem of keeping metadata in sync between the wrapper and inner tensor.
            # This also alleviates us from having to manually handle metadata mutations on the wrapper.
            if len(kwargs) != 0:
                raise AssertionError("kwargs must be empty for metadata functions")
            if func in [
                torch.ops.aten.is_strides_like_format.default,
                torch.ops.aten.is_contiguous.memory_format,
            ]:
                if len(args) != 2 or not isinstance(args[0], FunctionalTensor):
                    raise AssertionError("Expected 2 args with FunctionalTensor first")
                return func(torch._from_functional_tensor(args[0].elem), args[1])
            if len(args) != 1 or not isinstance(args[0], FunctionalTensor):
                raise AssertionError("Expected 1 arg with FunctionalTensor")

            return func(torch._from_functional_tensor(args[0].elem))
        # Originally I tried to implement my subclass without giving it a torch_dispatch, but I gave up:
        # - _make_wrapper_subclass requires a __torch_dispatch__
        # - If we want to use _make_subclass(), we have a problem: the subclass will share a TensorImpl with the inner tensor,
        #   which is of type FunctionalTensorWrapper! We explicitly do not want our wrapper to be a FunctionalTensorWrapper.
        # - If we use the default tensor.__new__(), we have another problem: it returns inner_tensor.alias(),
        #   which causes every subclass created above autograd to have autograd view metadata
        #   (in addition to also being a FunctionalTensorWrapper).
        raise RuntimeError(
            "Attempting to use FunctionalTensor on its own. Instead, please use it with a corresponding FunctionalTensorMode()"
        )