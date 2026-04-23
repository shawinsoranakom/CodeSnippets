def valid_binary(fn, a, b):
    if fn == "pow" and (
        # sympy will expand to x*x*... for integral b; don't do it if it's big
        b > 4
        # no imaginary numbers
        or a <= 0
        # 0**0 is undefined
        or (a == b == 0)
    ):
        return False
    elif fn == "pow_by_natural" and (
        # sympy will expand to x*x*... for integral b; don't do it if it's big
        b > 4
        or b < 0
        or (a == b == 0)
    ):
        return False
    elif fn == "mod" and (a < 0 or b <= 0):
        return False
    elif (fn in ["div", "truediv", "floordiv"]) and b == 0:
        return False
    return True