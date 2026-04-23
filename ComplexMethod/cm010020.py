def _reduce_ex_internal(self, proto):
        check_serializing_named_tensor(self)

        from torch.utils.hooks import warn_if_has_hooks

        # See Note [Don't serialize hooks]
        warn_if_has_hooks(self)
        backward_hooks: dict[Any, Any] = OrderedDict()

        skip_data = torch.serialization._serialization_tls.skip_data
        materialize_fake_tensors = (
            torch.serialization._serialization_tls.materialize_fake_tensors
        )

        if self.device.type in ["xla", "maia", "mtia"] or (
            not torch._C._has_storage(self)
            and self.device.type == torch._C._get_privateuse1_backend_name()
        ):
            if skip_data:
                raise RuntimeError(
                    "Cannot serialize tensors on backends with no storage under skip_data context manager"
                )
            cpu_tensor = self.cpu()
            return (
                torch._utils._rebuild_device_tensor_from_cpu_tensor,
                (cpu_tensor, self.dtype, str(self.device), self.requires_grad),
            )
        if self.device.type == "meta":
            # NB: This implementation BREAKS storage sharing.  Current
            # hypothesis is that no one cares for meta tensors.
            if skip_data:
                warnings.warn(
                    "Serializing tensors on the meta device under skip_data context manager is a no-op",
                    stacklevel=2,
                )
            arg_meta = (
                self.dtype,
                tuple(self.size()),
                self.stride(),
                self.requires_grad,
            )
            return (torch._utils._rebuild_meta_tensor_no_storage, arg_meta)
        if self.is_quantized:
            if skip_data:
                raise RuntimeError(
                    "Cannot serialize qtensor under skip_data context manager, file an issue if you need this feature"
                )
            # quantizer_params can be different type based on torch attribute
            quantizer_params: (
                tuple[torch.qscheme, float, int] | tuple[Any, Tensor, Tensor, int]
            )
            if self.qscheme() == torch.per_tensor_affine:
                quantizer_params = (
                    torch.per_tensor_affine,
                    self.q_scale(),
                    self.q_zero_point(),
                )
            elif self.qscheme() in (
                torch.per_channel_affine,
                torch.per_channel_affine_float_qparams,
            ):
                # convert scales and zero points to tuple to avoid recursive calls
                # when/if we get multi-axis quantized tensors in the future, the shape
                # is recoverable from the main tensor shape
                quantizer_params = (
                    torch.per_channel_affine,
                    self.q_per_channel_scales(),
                    self.q_per_channel_zero_points(),
                    self.q_per_channel_axis(),
                )
            else:
                raise RuntimeError(
                    f"Serialization is not supported for tensors of type {self.qscheme()}"
                )
            # TODO: Once we decide to break serialization FC, no longer
            # need to wrap with TypedStorage
            args_qtensor = (
                torch.storage.TypedStorage(
                    wrap_storage=self._typed_storage()._untyped_storage,
                    dtype=self.dtype,
                    _internal=True,
                ),
                self.storage_offset(),
                tuple(self.size()),
                self.stride(),
                quantizer_params,
                self.requires_grad,
                backward_hooks,
            )
            return (torch._utils._rebuild_qtensor, args_qtensor)
        elif self.is_sparse:
            if self.layout == torch.sparse_coo:
                args_sparse = (
                    self.layout,
                    (self._indices(), self._values(), self.size(), self.is_coalesced()),
                )
            else:
                raise NotImplementedError(
                    f"sparse tensor __reduce_ex__ for layout `{self.layout}`"
                )
            return (torch._utils._rebuild_sparse_tensor, args_sparse)
        elif self.layout in {
            torch.sparse_csr,
            torch.sparse_csc,
            torch.sparse_bsr,
            torch.sparse_bsc,
        }:
            if self.layout in {torch.sparse_csr, torch.sparse_bsr}:
                compressed_indices, plain_indices = (
                    self.crow_indices(),
                    self.col_indices(),
                )
            else:
                compressed_indices, plain_indices = (
                    self.ccol_indices(),
                    self.row_indices(),
                )
            args_sparse_compressed = (
                self.layout,
                (
                    compressed_indices,
                    plain_indices,
                    self.values(),
                    self.size(),
                ),
            )
            return (torch._utils._rebuild_sparse_tensor, args_sparse_compressed)
        elif self.is_nested:
            if skip_data:
                raise RuntimeError(
                    "Cannot serialize nested tensor under skip_data context manager, file an issue if you need this feature"
                )
            args_nested = (
                # NB: values() currently returns the storage as a buffer in an unsafe way.
                # Ideally, we'd use a private API for this instead. TODO: Switch to this if
                # we ever get around to adding it.
                self.values(),
                self._nested_tensor_size(),
                self._nested_tensor_strides(),
                self._nested_tensor_storage_offsets(),
            )
            return (torch._utils._rebuild_nested_tensor, args_nested)
        elif (
            type(self) is not torch.Tensor
            and type(self).__torch_dispatch__ is not torch.Tensor.__torch_dispatch__
            and (
                isinstance(self, torch._subclasses.functional_tensor.FunctionalTensor)
                or (
                    not isinstance(self, torch._subclasses.fake_tensor.FakeTensor)
                    and self.data_ptr() == 0
                )
            )
        ):
            arg_wrapper_subclass = (
                type(self),
                self.dtype,
                tuple(self.size()),
                self.stride(),
                self.storage_offset(),
                self.layout,
                self.device,
                self.requires_grad,
            )
            return (torch._utils._rebuild_wrapper_subclass, arg_wrapper_subclass)
        elif (
            type(self) is not torch.Tensor
            and type(self).__torch_dispatch__ is not torch.Tensor.__torch_dispatch__
            and (
                isinstance(self, torch._subclasses.fake_tensor.FakeTensor)
                and not (skip_data and materialize_fake_tensors)
            )
        ):
            arg_wrapper_subclass = (
                type(self),
                self.dtype,
                tuple(self.size()),
                self.stride(),
                self.storage_offset(),
                self.layout,
                self.device,
                self.requires_grad,
            )
            return (torch._utils._rebuild_wrapper_subclass, arg_wrapper_subclass)
        else:
            v3_dtypes = torch.storage._new_dtypes()
            if self.dtype in v3_dtypes:
                rebuild_func = torch._utils._rebuild_tensor_v3
                storage = self.untyped_storage()
            else:
                # TODO: Once we decide to break serialization FC, no longer
                # need to wrap with TypedStorage
                rebuild_func = torch._utils._rebuild_tensor_v2  # type: ignore[assignment]
                storage = torch.storage.TypedStorage(
                    wrap_storage=self._typed_storage()._untyped_storage,
                    dtype=self.dtype,
                    _internal=True,
                )  # type: ignore[assignment]

            # TODO: remove hasattr, it's a hack to support versions of torch that
            # don't have _subclasses
            if (
                hasattr(torch, "_subclasses")
                and isinstance(self, torch._subclasses.fake_tensor.FakeTensor)
                and skip_data
            ):
                storage._fake_device = self.device

            args = (
                storage,
                self.storage_offset(),
                tuple(self.size()),
                self.stride(),
                self.requires_grad,
                backward_hooks,
            )  # previously was self._backward_hooks

            if isinstance(storage, torch.storage.UntypedStorage):
                args = args + (self.dtype,)  # type: ignore[assignment]

            metadata = torch._utils.get_tensor_metadata(self)
            if metadata:
                args = args + (metadata,)  # type: ignore[assignment]

            return (rebuild_func, args)