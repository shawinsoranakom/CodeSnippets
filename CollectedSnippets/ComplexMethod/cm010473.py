def __torch_dispatch__(  # type: ignore[override] # TODO
        cls,
        func: OpOverload,
        types: Sequence[type],
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] = immutable_dict(),
    ) -> object:
        # need to handle here to avoid infinite recursion
        # see [in_kernel_invocation]
        if func is torch.ops.prim.device.default:
            if len(args) != 1 or not isinstance(args[0], FakeTensor):
                raise AssertionError(
                    "Expected exactly one FakeTensor argument for prim.device.default"
                )
            if args[0].fake_mode.in_kernel_invocation:
                return torch.device("meta")
            else:
                return args[0].fake_device

        # this handler must be done inside FakeTensor subclass, not mode, because
        # we can end up dispatching here when we have a fake tensor with
        # symbolic sizes running under in_kernel_invocation_manager.
        # The subclass is asked to handle this query because size (not
        # sym_size) was called, but we are unable to serve it directly because
        # there are symbolic sizes in the class.  The use of
        # in_kernel_invocation_manager means it's incorrect to activate a
        # mode to actually handle this (this caused
        # https://github.com/pytorch/pytorch/issues/122772).
        if handler := _DISPATCH_META_HANDLERS.get(func):
            return handler(args)

        # Because fake mode can return NotImplemented (if it sees a subclass
        # it doesn't know how to deal with), this test here is important
        # because the next dispatch after a fake mode will attempt to use
        # subclasses of tensors to dispatch, and any FakeTensor arguments
        # will be considered eligible.
        unrecognized_types = [
            t for t in types if not issubclass(t, FakeTensor) and t is not Tensor
        ]
        if unrecognized_types:
            not_implemented_log.debug(
                "FakeTensor unrecognized subclass(es): %s", unrecognized_types
            )
            return NotImplemented

        fake_mode = None
        for arg in pytree.arg_tree_leaves(*args, **kwargs):
            if isinstance(arg, FakeTensor):
                fake_mode = arg.fake_mode
                break

        if fake_mode is None:
            raise AssertionError("Could not find a FakeTensor in the arguments")

        # If the fake mode is already active, don't try to reapply it!
        # NotImplemented is the right thing to return here, because the
        # typical situation this can occur is if ProxyTensorMode returned a
        # NotImplemented because of a not implemented subclass; we may have
        # unluckily attempted to hit FakeTensor's dispatch first,
        # NotImplemented lets us keep chaining until we find the actual
        # subclass
        maybe_cur_fake_mode = torch._C._get_dispatch_mode(
            torch._C._TorchDispatchModeKey.FAKE
        )
        if maybe_cur_fake_mode:
            not_implemented_log.debug(
                "FakeTensor mode already active: %s in %s",
                fake_mode,
                maybe_cur_fake_mode,
            )
            return NotImplemented

        if fake_mode.in_kernel_invocation:
            raise AssertionError("fake_mode.in_kernel_invocation must be False")

        with fake_mode:
            return func(*args, **kwargs)