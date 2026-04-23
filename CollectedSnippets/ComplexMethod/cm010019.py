def __deepcopy__(self, memo):
        if has_torch_function_unary(self):
            return handle_torch_function(Tensor.__deepcopy__, (self,), self, memo)
        if not self.is_leaf:
            raise RuntimeError(
                "Only Tensors created explicitly by the user "
                "(graph leaves) support the deepcopy protocol at the moment.  "
                "If you were attempting to deepcopy a module, this may be because "
                "of a torch.nn.utils.weight_norm usage, "
                "see https://github.com/pytorch/pytorch/pull/103001"
            )
        if id(self) in memo:
            return memo[id(self)]
        with torch.no_grad():
            # TODO: skipping storage copy is wrong for meta, as meta
            # does accurate alias tracking; however, the code below
            # doesn't work because of
            # https://github.com/pytorch/pytorch/issues/47442
            # Update the test in test_serialization if you remove 'meta' from here
            if (
                self.is_sparse
                or self.device.type
                in ["lazy", "xla", "mtia", "mps", "maia", "meta", "ipu"]
                or (
                    not torch._C._has_storage(self)
                    and self.device.type == torch._C._get_privateuse1_backend_name()
                )
                or (type(self) is not Tensor and self.data_ptr() == 0)
            ):
                new_tensor = self.clone()
                if type(new_tensor) is not type(self):
                    raise RuntimeError(
                        "The default implementation of __deepcopy__() for wrapper subclasses "
                        "only works for subclass types that implement clone() and for which "
                        "cloning returns another instance of the same subclass. You should either "
                        "properly implement clone() for your subclass or override __deepcopy__() "
                        "if it is intended behavior for clone() to return an instance of a "
                        "different type."
                    )
            else:
                new_storage = self._typed_storage()._deepcopy(memo)
                if self.is_quantized:
                    # quantizer_params can be different type based on torch attribute
                    quantizer_params: (
                        tuple[torch.qscheme, float, int]
                        | tuple[torch.qscheme, Tensor, Tensor, int]
                    )
                    if self.qscheme() == torch.per_tensor_affine:
                        quantizer_params = (
                            self.qscheme(),
                            self.q_scale(),
                            self.q_zero_point(),
                        )
                    elif self.qscheme() in (
                        torch.per_channel_affine,
                        torch.per_channel_affine_float_qparams,
                    ):
                        quantizer_params = (
                            self.qscheme(),
                            self.q_per_channel_scales(),
                            self.q_per_channel_zero_points(),
                            self.q_per_channel_axis(),
                        )
                    else:
                        raise RuntimeError(
                            f"Unsupported qscheme {self.qscheme()} in deepcopy"
                        )
                    # TODO: Once we decide to break serialization FC, no longer
                    # need to wrap with TypedStorage
                    new_tensor = torch._utils._rebuild_qtensor(
                        torch.storage.TypedStorage(
                            wrap_storage=new_storage._untyped_storage,
                            dtype=self.dtype,
                            _internal=True,
                        ),
                        self.storage_offset(),
                        self.size(),
                        self.stride(),
                        quantizer_params,
                        self.requires_grad,
                        self._backward_hooks,
                    )
                    if type(new_tensor) is not type(self):
                        raise RuntimeError(
                            "The default implementation of __deepcopy__() for quantized tensors "
                            "expects the tensor returned by torch._utils._rebuild_qtensor() to "
                            "match the type of the instance being copied. If you encounter this, "
                            "please open an issue on PyTorch's GitHub."
                        )
                else:
                    new_tensor = self.new_empty([])
                    if type(new_tensor) is not type(self):
                        raise RuntimeError(
                            "The default implementation of __deepcopy__() for non-wrapper subclasses "
                            "only works for subclass types that implement new_empty() and for which "
                            "that function returns another instance of the same subclass. You should "
                            "either properly implement new_empty() for your subclass or override "
                            "__deepcopy__() if it is intended behavior for new_empty() to return "
                            "an instance of a different type."
                        )
                    new_tensor.set_(
                        new_storage, self.storage_offset(), self.size(), self.stride()
                    )
                    if self.is_conj():
                        new_tensor = new_tensor.conj_physical()
                    if self.is_neg():
                        new_tensor = new_tensor.neg()
            if self.requires_grad:
                new_tensor.requires_grad_()
            if self.grad is not None:
                new_tensor.grad = self.grad.__deepcopy__(memo)

            if type(self) is not Tensor:
                if type(new_tensor) is not type(self):
                    raise RuntimeError(
                        "Type of deepcopy result does not match the type of the source tensor. "
                        "If you encounter this, please open an issue on PyTorch's GitHub."
                    )

                # Plain Tensors don't have slots
                slots_to_save = copyreg._slotnames(self.__class__)  # type: ignore[attr-defined]
                for slot in slots_to_save:
                    if hasattr(self, slot):
                        setattr(new_tensor, slot, deepcopy(getattr(self, slot), memo))

            # don't try to deepcopy non-serializable cached data
            self._clear_non_serializable_cached_data()
            new_tensor.__dict__ = deepcopy(self.__dict__, memo)

            memo[id(self)] = new_tensor
            return new_tensor