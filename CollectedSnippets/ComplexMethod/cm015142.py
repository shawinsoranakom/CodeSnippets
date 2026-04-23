def tensorfn_inplace(t0, t1, t2=None):
            t0_fn = getattr(t0, fn + "_")
            if fn == "lerp":
                return t0_fn(t1, 0.5)
            elif fn == "masked_scatter":
                return t0_fn(t1 < 0.5, full1d)
            elif fn == "masked_fill":
                return t0_fn(t1 < 0.5, 1.0)
            elif fn == "map":
                return t0_fn(t1, lambda x, y: x + y)
            elif fn == "map2":
                return t0_fn(t1, t2, lambda x, y, z: x + y + z)
            elif fn in fns_3_args:
                return t0_fn(1.0, t1, t2)
            elif fn in fns_value_kwarg:
                return t0_fn(t1, t2, value=1.0)
            else:
                return t0_fn(t1)