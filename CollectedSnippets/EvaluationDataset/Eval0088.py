def decimal_to_binary_recursive_helper(decimal: int) -> str:

    decimal = int(decimal)
    if decimal in (0, 1):  
        return str(decimal)
    div, mod = divmod(decimal, 2)
    return decimal_to_binary_recursive_helper(div) + str(mod)
