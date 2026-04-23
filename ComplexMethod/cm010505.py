def describe_tensor(
        self, t: torch.Tensor, *, recurse: bool = True, trace: bool = False
    ) -> MetaTensorDesc[Any]:
        is_leaf = safe_is_leaf(t)
        is_view = t._is_view()
        is_sparse = t.is_sparse
        layout = t.layout
        is_nested = t.is_nested
        is_traceable_wrapper_subclass_v = is_traceable_wrapper_subclass(t)
        is_functorch_wrapped = is_functorch_wrapped_tensor(t)
        is_mkldnn = t.is_mkldnn
        is_batchedtensor_v = is_batchedtensor(t)
        is_legacy_batchedtensor_v = is_legacy_batchedtensor(t)
        is_gradtrackingtensor_v = is_gradtrackingtensor(t)
        is_functional = torch._is_functional_tensor(t)

        storage = None
        # NB: For compatibility, I default this to zero, as sometimes people
        # still have stuffed zero into storage offset even though the tensor
        # doesn't meaningfully have an offset
        storage_offset = 0
        if not (
            is_sparse
            or is_sparse_compressed_layout(layout)
            or (is_nested and not is_traceable_wrapper_subclass_v)
            or is_mkldnn
            # TODO: TBH, functorch wrapped tensors probably should have
            # storage associated with them
            or is_functorch_wrapped
            or is_legacy_batchedtensor_v
        ):
            # NB: We actually don't use storage to do views, but might as well
            # put it in for accuracy
            storage = self.describe_storage(t.untyped_storage(), trace=trace)
            storage_offset = t.storage_offset()  # type: ignore[assignment]

        stride = None
        if not (
            is_sparse
            or is_sparse_compressed_layout(layout)
            or (is_nested and not is_traceable_wrapper_subclass_v)
        ):
            # stride/storage_offset are called from is_functorch_wrapped,
            # view_from_base, empty_create_subclass,
            # sym_sizes_strides_storage_offset (empty_create)
            stride = t.stride()

        # NB: this technically should refer to functorch unwrapped tensor, but
        # I am (perhaps abusively) using it to store both the functorch and
        # non-functorch functional tensor
        unwrapped = None
        autograd_meta_from = None
        current_level = None
        if is_batchedtensor_v or is_gradtrackingtensor_v:
            unwrapped = self.describe_tensor(get_unwrapped(t), trace=trace)
        # xla and lazy tensors present as functional tensors, but we want them
        # to be handled specially
        elif is_functional and t.device.type not in ("xla", "lazy"):
            if t._is_view():
                raise RuntimeError(
                    "Cannot safely fakify a view because this process drops the view information right now."
                )
            if not is_functorch_wrapped:
                torch._sync(t)
                unwrapped = self.describe_tensor(
                    torch._from_functional_tensor(t), trace=trace
                )
                autograd_meta_from = t
            else:
                reapply_views = torch._C._functionalization_reapply_views_tls()
                # NB: has side effects!
                unwrapped = self.describe_tensor(
                    _unwrap_functional_tensor(t, reapply_views), trace=trace
                )
                # TODO: It's pretty suspicious that functional tensors don't have
                # valid level and thus we just grab whatever the current level
                # is
                current_level = torch._C._functorch.current_level()

        maybe_functorch_stack = None
        if is_functorch_wrapped:
            with (
                torch._functorch.pyfunctorch.temporarily_clear_interpreter_stack()
            ) as maybe_functorch_stack:
                pass

        attrs = None
        opaque_attrs = None
        ctx = None
        type_v = None
        if is_traceable_wrapper_subclass_v:
            if not hasattr(t, "__tensor_flatten__"):
                raise AssertionError(
                    "Traceable wrapper subclass must have __tensor_flatten__ method"
                )
            raw_attrs, ctx = t.__tensor_flatten__()
            attrs = {}
            opaque_attrs = {}
            for attr in raw_attrs:
                inner = getattr(t, attr)
                match inner:
                    case torch.Tensor():
                        attrs[attr] = self.describe_tensor(inner, trace=trace)
                    case OpaqueBase():
                        from torch._library.fake_class_registry import (
                            maybe_unwrap_fake_script_object,
                        )

                        opaque_attrs[attr] = maybe_unwrap_fake_script_object(inner)
                    case _:
                        raise AssertionError(
                            f"expected Tensor or OpaqueBase, got {type(inner)}"
                        )
            type_v = type(t)

        from torch.nested._internal.nested_tensor import _tensor_symint_registry

        view_func = ViewFunc.from_tensor(t)

        # TODO: Is it important to enable torch.inference_mode before querying
        # these values?
        is_inference_mode_disabled = getattr(tls, "disable_inference_mode", False)
        r: MetaTensorDesc[Any] = MetaTensorDesc(
            id=self.get_tensor_id(t),
            storage=storage,
            is_inference=False if is_inference_mode_disabled else t.is_inference(),
            is_leaf=is_leaf,
            requires_grad=t.requires_grad,
            # NB: ndim should be OK too but there is a disaster at
            # python test/dynamo/test_subclasses.py -k test_user_overridden_property_unsupported
            # Actually, this means that we have a little bit of a problem
            # here, which is that there is some sensitivity to how exactly an
            # access is done if you have a __torch_function__ subclass.  Maybe
            # should disable torch function before doing accesses?
            ndim=t.dim(),
            dtype=t.dtype,
            is_sparse=is_sparse,
            is_mkldnn=is_mkldnn,
            is_functorch_wrapped=is_functorch_wrapped,
            is_batchedtensor=is_batchedtensor_v,
            is_legacy_batchedtensor=is_legacy_batchedtensor_v,
            is_gradtrackingtensor=is_gradtrackingtensor_v,
            is_view=is_view,
            is_conj=t.is_conj(),
            is_neg=t.is_neg(),
            is_parameter=isinstance(t, torch.nn.Parameter),
            is_traceable_wrapper_subclass=is_traceable_wrapper_subclass_v,
            is_nested=is_nested,
            nested_int=(
                _tensor_symint_registry[t].node.nested_int()
                if t in _tensor_symint_registry
                else None
            ),
            is_functional=is_functional,
            layout=layout,
            device=t.device,
            size=t.size(),
            stride=stride,
            # pyrefly: ignore [bad-argument-type]
            storage_offset=storage_offset,
            dynamo_dynamic_indices=list(getattr(t, "_dynamo_dynamic_indices", set())),
            dynamo_hint_overrides=getattr(t, "_dynamo_hint_overrides", {}),
            sparse_dim=(
                t.sparse_dim() if t.is_sparse or is_sparse_compressed(t) else None
            ),
            dense_dim=t.dense_dim() if t.is_sparse or is_sparse_compressed(t) else None,
            is_coalesced=t.is_coalesced() if t.is_sparse else None,
            # TODO: I actually think recursing here is correct, but we have at
            # least an infinite cycle from base -> values -> base
            # https://github.com/pytorch/pytorch/issues/122089
            crow_indices=(
                self.describe_tensor(t.crow_indices(), recurse=False, trace=trace)
                if recurse and t.layout in {torch.sparse_csr, torch.sparse_bsr}
                else None
            ),
            col_indices=(
                self.describe_tensor(t.col_indices(), recurse=False, trace=trace)
                if recurse and t.layout in {torch.sparse_csr, torch.sparse_bsr}
                else None
            ),
            ccol_indices=(
                self.describe_tensor(t.ccol_indices(), recurse=False, trace=trace)
                if recurse and t.layout in {torch.sparse_csc, torch.sparse_bsc}
                else None
            ),
            row_indices=(
                self.describe_tensor(t.row_indices(), recurse=False, trace=trace)
                if recurse and t.layout in {torch.sparse_csc, torch.sparse_bsc}
                else None
            ),
            values=(
                self.describe_tensor(t.values(), recurse=False, trace=trace)
                if recurse and is_sparse_compressed(t)
                else None
            ),
            grad=(
                self.describe_tensor(grad, trace=trace)
                if (grad := safe_grad(t)) is not None
                else None
            ),
            creation_meta=(
                torch._C._autograd._get_creation_meta(t) if t._is_view() else None
            ),
            unwrapped=unwrapped,
            level=(
                maybe_get_level(t)
                if is_batchedtensor_v or is_gradtrackingtensor_v
                else None
            ),
            bdim=maybe_get_bdim(t) if is_batchedtensor_v else None,
            base=(
                self.describe_tensor(t._base, trace=trace)
                if recurse and t._is_view() and t._base is not None
                else None
            ),
            fake_mode=torch._subclasses.fake_tensor.maybe_get_fake_mode(t),
            view_func=view_func,
            # pyrefly: ignore [bad-argument-type]
            attrs=attrs,
            opaque_attrs=opaque_attrs if opaque_attrs else None,
            ctx=ctx,
            type=type_v,
            # NB: even if functorch is enabled, don't actually save the
            # interpreter stack here unless we are actually functorch wrapped;
            # it's irrelevant for non-functorch stuff
            functorch_stack=maybe_functorch_stack,
            autograd_meta_from=autograd_meta_from,
            current_level=current_level,
            data=t if self.copy_data else None,
        )
        if trace and r.id not in self.traced_tensors:
            trace_structured(
                "describe_tensor",
                metadata_fn=lambda: r.as_json(self.id),
            )
            self.traced_tensors.add(r.id)
        return r