def right_inverse(self, value: Tensor) -> None:
        r"""Call the ``right_inverse`` methods of the parametrizations in the inverse registration order.

        Then, it stores the result in ``self.original`` if ``right_inverse`` outputs one tensor
        or in ``self.original0``, ``self.original1``, ... if it outputs several.

        Args:
            value (Tensor): Value to which initialize the module
        """
        # All the exceptions in this function should almost never throw.
        # They could throw if, for example, right_inverse function returns a different
        # dtype when given a different input, which should most likely be caused by a
        # bug in the user's code

        with torch.no_grad():
            # See https://github.com/pytorch/pytorch/issues/53103
            for module in reversed(self):  # type: ignore[call-overload]
                if hasattr(module, "right_inverse"):
                    value = module.right_inverse(value)  # type: ignore[operator]
                else:
                    raise RuntimeError(
                        f"parametrization {type(module).__name__} does not implement "
                        "right_inverse."
                    )
            if self.is_tensor:
                # These exceptions should only throw when a right_inverse function does not
                # return the same dtype for every input, which should most likely be caused by a bug
                if not isinstance(value, Tensor):
                    raise ValueError(
                        f"`right_inverse` should return a tensor. Got {type(value).__name__}"
                    )
                if value.dtype != self.original.dtype:
                    raise ValueError(
                        f"The tensor returned by `right_inverse` has dtype {value.dtype} "
                        f"while `original` has dtype {self.original.dtype}"
                    )
                # We know that the result is going to have the same dtype
                _maybe_set(self.original, value)
            else:
                if not isinstance(value, collections.abc.Sequence):
                    raise ValueError(
                        "'right_inverse' must return a sequence of tensors. "
                        f"Got {type(value).__name__}."
                    )
                if len(value) != self.ntensors:
                    raise ValueError(
                        "'right_inverse' must return a sequence of tensors of length "
                        f"{self.ntensors}. Got a sequence of length {len(value)}."
                    )
                for i, tensor in enumerate(value):
                    original_i = getattr(self, f"original{i}")
                    match tensor:
                        case OpaqueBase():
                            if is_opaque_reference_type(type(tensor)):
                                setattr(self, f"original{i}", tensor)
                                continue
                            # Fall-through
                        case Tensor():
                            if original_i.dtype != tensor.dtype:
                                raise ValueError(
                                    f"Tensor {i} returned by `right_inverse` has dtype {tensor.dtype} "
                                    f"while `original{i}` has dtype {original_i.dtype}"
                                )
                            _maybe_set(original_i, tensor)
                            continue
                    raise ValueError(
                        f"'right_inverse' must return a sequence of tensors "
                        f"or reference-type opaques. Got element {i} of type "
                        f"{type(tensor).__name__}."
                    )