def run_meta_crossref(
    test_case,
    test_expect,
    func,
    args,
    kwargs,
    *,
    dtype,
    device_type,
    run_symbolic_meta: bool
):
    to_meta = MetaConverter()
    do_meta = test_expect is not TestExpect.SKIP
    if do_meta:
        try:
            meta_args = tree_map(to_meta, args)
            meta_kwargs = tree_map(to_meta, kwargs)
        except Exception as e:
            raise RuntimeError(
                f"failed to convert args to meta; "
                f"originally (*{args}, **{kwargs})") from e
    try:
        rs = func(*args, **kwargs)
    except Exception as e:
        raise AssertionError("Original OpInfo is broken") from e

    # TODO: also handle cases where func raise an exception

    # For now, only attempt if we managed to convert all tensor types
    # (if any of them failed, we're in a mixed device situation and
    # this isn't well supported)
    if do_meta and to_meta.successful():
        # Special cases
        if func is torch.tensor_split:
            # Use original indices_or_sections, this argument is data dependent
            meta_args = (meta_args[0], args[1]) + meta_args[2:]
        elif func is torch.Tensor.__getitem__:
            # Ensure boolean tensors use original
            if len(args) != 2:
                raise AssertionError(f"expected len(args) == 2, got {len(args)}")
            flat_args = pytree.tree_leaves(args[1])
            flat_meta_args, spec = tree_flatten(meta_args[1])
            flat_new_args = []
            for a, ma in zip(flat_args, flat_meta_args):
                flat_new_args.append(a if isinstance(a, torch.Tensor) and a.dtype in [torch.int8, torch.bool] else ma)
            meta_args = (meta_args[0], tree_unflatten(flat_new_args, spec))
        elif func in (torch.ops.aten.repeat_interleave.Tensor, torch.ops.aten.repeat_interleave.Tensor_out):
            if kwargs.get("output_size", None) is None:
                meta_args = args
                if func is torch.ops.aten.repeat_interleave.Tensor_out:
                    meta_kwargs["out"] = kwargs["out"]
        elif func in (torch.ops.aten.index.Tensor, torch.ops.aten.index.Tensor_out):
            # Don't convert boolean tensors to meta as they will have nonzero
            # called on them
            indices = []
            for meta_index, real_index in zip(meta_args[1], args[1]):
                if meta_index is not None and meta_index.dtype in [torch.int8, torch.bool]:
                    indices.append(real_index)
                else:
                    indices.append(meta_index)
            meta_args = (meta_args[0], indices)
        elif func is torch.nn.functional.ctc_loss and all([isinstance(args[2], list), isinstance(args[3], list)]):
            # torch.ops.aten._ctc_loss.IntList has a meta kernel but
            # torch.ops.aten._ctc_loss.Tensor does not
            test_expect = TestExpect.SUCCESS

        if kwargs.get("device", None) is not None:
            meta_kwargs["device"] = "meta"

        try:
            # Suppress warnings, this doesn't matter for test_meta.py
            # but it does matter if you want to use this decorator
            # for cross-ref testing, as some tests may be looking at
            # errors
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if run_symbolic_meta:
                    # Run the decomps and meta kernels registered
                    # to the python dispatcher instead of the regular dispatcher.
                    # This should be the same set of kernels
                    # that fake tensor runs in dynamic shapes mode.
                    with enable_python_dispatcher():
                        meta_rs = func(*meta_args, **meta_kwargs)
                else:
                    meta_rs = func(*meta_args, **meta_kwargs)
        except Exception as e:
            if test_expect is TestExpect.XFAILURE:
                return rs
            seen_failed.setdefault(func, set()).add(dtype)
            if isinstance(e, NotImplementedError):
                m = RE_NOT_IMPLEMENTED_MSG.search(e.args[0])
                if m:
                    failed_reasons[func].add(m.group(1))
            if COLLECT_EXPECT:
                return rs
            raise RuntimeError(f"""\
failed to run: {resolve_name(func)}(
*{verbose_print(meta_args)},
**{verbose_print(meta_kwargs)}
)""") from e
        else:
            try:
                delim = ',\n  '
                assert_ref_meta_equal(test_case, func, meta_rs, rs, lambda msg: f"""\
meta disagrees with real impl:
{resolve_name(func)}(
  {delim.join(map(verbose_print, meta_args))},
  {delim.join(k + ": " + verbose_print(v) for k, v in meta_kwargs.items())}
) = (
  {verbose_print(meta_rs)}
)
{msg}
""")
            except Exception:
                if test_expect is TestExpect.XFAILURE:
                    return rs
                seen_failed.setdefault(func, set()).add(dtype)
                if COLLECT_EXPECT:
                    return rs
                raise
            else:
                seen_succeeded.setdefault(func, set()).add(dtype)
                if test_expect is TestExpect.XFAILURE and not COLLECT_EXPECT:
                    raise RuntimeError(f"unexpected success {resolve_name(func)} {meta_args} {meta_kwargs}")

    return rs