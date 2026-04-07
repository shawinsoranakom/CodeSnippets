def func(a, *, b=1, **kwargs):
                c = kwargs.get("c")
                return a, b, c