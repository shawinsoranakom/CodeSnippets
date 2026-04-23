def __torch_dispatch__(self, func, types, args=(), kwargs=None):
            def unwrap(e):
                return e.elem if isinstance(e, CompositeCompliantTensor) else e

            def wrap(e):
                return CompositeCompliantTensor(e, self) if isinstance(e, torch.Tensor) else e

            if func is torch.ops.aten._local_scalar_dense.default:
                raise RuntimeError(
                    ".item() is not allowed to be called inside of composite "
                    "functions in the PyTorch library because not all backends "
                    "and/or Tensor subclasses (e.g. vmap, ProxyTensor) support them.")

            if func.overloadpacket.__name__ in ('set_', 'resize_'):
                raise RuntimeError(
                    f"{func.__name__} is not allowed to be called inside of "
                    f"Composite operators.")

            if is_inplace(func):
                # NB: We are making an assumption that if the function is in-place,
                # then the first argument is being written to. Introspection please save us!
                mutated_argument = args[0]
                if not isinstance(mutated_argument, CompositeCompliantTensor) and \
                        any(isinstance(a, CompositeCompliantTensor) for a in args[1:]):
                    raise RuntimeError(
                        'Not composite compliant: performing in-place operation '
                        f'{func.__name__} where the Tensor being written to is '
                        'regular Tensor but the other tensors are Tensor Subclasses. '
                        'Please try to avoid this in-place operation.')

            unwrapped_args = tree_map(unwrap, args)
            unwrapped_kwargs = tree_map(unwrap, kwargs)
            unwrapped_rs = func(*unwrapped_args, **unwrapped_kwargs)
            rs = tree_map(wrap, unwrapped_rs)

            if is_view_fn(func) and autograd_view_consistency:
                # Note [Alias Result]
                # Autograd asserts that for B = A.view_fn(...), B and A's storages
                # are the same. Here we try to make B alias A to avoid those asserts.
                # See https://github.com/pytorch/pytorch/issues/65339 for more information
                # about the issue.
                with no_dispatch():
                    # Idea: this is a weird way of getting a storage that aliases the input.
                    # This is a workaround for #65339.
                    # 1. under no_dispatch, all of the wrapper tensors look like regular
                    #    tensors with special storage (the storage is nullptr and
                    #    advertises CPU/CUDA device.
                    # 2. we run func, which ends up running the view operation
                    # 3. All view operations reuse the input's storage and return
                    #    result Tensor(s) with new sizes/strides/offset that alias
                    #    the input.
                    # 4. we set the storage (and sizes/strides/offset) of the wrapper
                    #    tensor results to be that of the tensors that alias the input
                    result = func(*args, **kwargs)
                    if isinstance(result, (tuple, list)):
                        for a, b in zip(rs, result, strict=True):
                            a.set_(b)
                    else:
                        rs.set_(result)

            # Some operations are allowed to in-place modify the metadata of the
            # inputs. The only ones are the "inplace view functions"; when we
            # run into these, we manually modify the metadata of the input.
            with no_dispatch():
                if is_inplace_view_fn(func):
                    func(*args, **kwargs)

            # For each CompositeCompliantTensor t, we check that t and t.elem
            # have consistent metadata. If they don't have consistent metadata,
            # that means the operator did something fishy.
            check = partial(check_metadata_consistency, CCT=CompositeCompliantTensor)
            pytree.tree_map_(check, args)
            pytree.tree_map_(check, kwargs)
            pytree.tree_map_(check, rs)
            return rs