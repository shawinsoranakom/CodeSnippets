def find_primitive(modulus: int) -> int | None:
    
    for r in range(1, modulus):
        li = []
        for x in range(modulus - 1):
            val = pow(r, x, modulus)
            if val in li:
                break
            li.append(val)
        else:
            return r
    return None
