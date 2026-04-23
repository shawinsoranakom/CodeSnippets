def is_dynamic(*args: Any) -> bool:
    from . import ir

    for t in args:
        if isinstance(
            t, (ir.TensorBox, ir.StorageBox, ir.BaseView, ir.ComputedBuffer, ir.Buffer)
        ):
            if has_free_symbols(t.maybe_get_size() or ()) or has_free_symbols(
                t.maybe_get_stride() or ()
            ):
                return True
        elif not isinstance(t, ir.IRNode):
            continue
        else:
            raise TypeError(f"unexpected type for is_dynamic {type(t)}")

    return False