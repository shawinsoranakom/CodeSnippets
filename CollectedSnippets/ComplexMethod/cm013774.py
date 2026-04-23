def __init__(
        self,
        modules: Sequence[Module],
        original: Tensor | Parameter,
        unsafe: bool = False,
    ) -> None:
        # We require this because we need to treat differently the first parametrization
        # This should never throw, unless this class is used from the outside
        if len(modules) == 0:
            raise ValueError("ParametrizationList requires one or more modules.")

        super().__init__(modules)
        self.unsafe = unsafe

        # In plain words:
        # module.weight must keep its dtype and shape.
        # Furthermore, if there is no right_inverse or the right_inverse returns a tensor,
        # this should be of the same dtype as the original tensor
        #
        # We check that the following invariants hold:
        #    X = module.weight
        #    Y = param.right_inverse(X)
        #    assert isinstance(Y, Tensor) or
        #           (isinstance(Y, collections.abc.Sequence) and all(isinstance(t, Tensor) for t in Y))
        #    Z = param(Y) if isinstance(Y, Tensor) else param(*Y)
        #    # Consistency checks
        #    assert X.dtype == Z.dtype and X.shape == Z.shape
        #    # If it has one input, this allows to be able to use set_ to be able to
        #    # move data to/from the original tensor without changing its id (which is what the
        #    # optimizer uses to track parameters)
        #    if isinstance(Y, Tensor)
        #      assert X.dtype == Y.dtype
        # Below we use original = X, new = Y

        original_shape = original.shape
        original_dtype = original.dtype

        # Compute new
        with torch.no_grad():
            new = original
            for module in reversed(self):  # type: ignore[call-overload]
                if hasattr(module, "right_inverse"):
                    try:
                        new = module.right_inverse(new)  # type: ignore[operator]
                    except NotImplementedError:
                        pass
                # else, or if it throws, we assume that right_inverse is the identity

        if not isinstance(new, Tensor) and not isinstance(new, Sequence):
            raise ValueError(
                "'right_inverse' must return a Tensor or a Sequence of tensors (list, tuple...). "
                f"Got {type(new).__name__}"
            )

        # Set the number of original tensors
        self.is_tensor = isinstance(new, Tensor)
        self.ntensors = 1 if self.is_tensor else len(new)

        # Register the tensor(s)
        if self.is_tensor:
            # pyrefly: ignore [missing-attribute]
            if original.dtype != new.dtype:
                raise ValueError(
                    "When `right_inverse` outputs one tensor, it may not change the dtype.\n"
                    f"original.dtype: {original.dtype}\n"
                    # pyrefly: ignore [missing-attribute]
                    f"right_inverse(original).dtype: {new.dtype}"
                )

            # pyrefly: ignore [missing-attribute]
            if original.device != new.device:
                raise ValueError(
                    "When `right_inverse` outputs one tensor, it may not change the device.\n"
                    f"original.device: {original.device}\n"
                    # pyrefly: ignore [missing-attribute]
                    f"right_inverse(original).device: {new.device}"
                )

            # Set the original to original so that the user does not need to re-register the parameter
            # manually in the optimiser
            with torch.no_grad():
                # pyrefly: ignore [bad-argument-type]
                _maybe_set(original, new)
            _register_parameter_or_buffer(self, "original", original)
        else:
            for i, originali in enumerate(new):
                match originali:
                    case OpaqueBase():
                        if not is_opaque_reference_type(type(originali)):
                            raise ValueError(
                                f"'right_inverse' must return a Tensor or a reference-type "
                                f"opaque. Got element {i} of the sequence with type "
                                f"{type(originali).__name__}."
                            )
                        setattr(self, f"original{i}", originali)
                    case Tensor():
                        # If the original tensor was a Parameter that required grad, we expect the user to
                        # add the new parameters to the optimizer after registering the parametrization
                        # (this is documented)
                        if isinstance(original, Parameter):
                            originali = Parameter(originali, original.requires_grad)
                        originali.requires_grad_(original.requires_grad)
                        _register_parameter_or_buffer(self, f"original{i}", originali)
                    case _:
                        raise ValueError(
                            "'right_inverse' must return a Tensor or a Sequence of tensors "
                            "(list, tuple...). "
                            f"Got element {i} of the sequence with type {type(originali).__name__}."
                        )

        if not self.unsafe:
            # Consistency checks:
            # Since f : A -> B, right_inverse : B -> A, Z and original should live in B
            # Z = forward(right_inverse(original))
            Z = self()
            if not isinstance(Z, Tensor):
                raise ValueError(
                    f"A parametrization must return a tensor. Got {type(Z).__name__}."
                )
            if Z.dtype != original_dtype:
                raise ValueError(
                    "Registering a parametrization may not change the dtype of the tensor, unless `unsafe` flag is enabled.\n"
                    f"unparametrized dtype: {original_dtype}\n"
                    f"parametrized dtype: {Z.dtype}"
                )
            if Z.shape != original_shape:
                raise ValueError(
                    "Registering a parametrization may not change the shape of the tensor, unless `unsafe` flag is enabled.\n"
                    f"unparametrized shape: {original_shape}\n"
                    f"parametrized shape: {Z.shape}"
                )