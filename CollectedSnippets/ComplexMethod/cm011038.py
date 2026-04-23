def shape_div(a: IntTuple, b: IntTuple) -> IntTuple:
    if is_tuple(a):
        if is_tuple(b):  # tuple tuple
            if len(a) != len(b):
                raise AssertionError
            return tuple(shape_div(x, y) for x, y in zip(a, b))
        else:  # tuple "int"
            # r = [shape_div(a[0],b)] + [shape_div(a[i],b := shape_div(b, product(a[i-1]))) for i in range(1,len(a))]
            r = []
            for v in a:
                r.append(shape_div(v, b))
                b = shape_div(b, product(v))
            return tuple(r)
    else:
        if is_tuple(b):  # "int" tuple
            return shape_div(a, product(b))
        else:  # "int" "int"
            if not (a % b == 0 or b % a == 0):
                raise AssertionError
            return (a + b - 1) // b