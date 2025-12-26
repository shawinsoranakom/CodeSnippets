def product_sum(arr: list[int | list], depth: int) -> int:

    total_sum = 0
    for ele in arr:
        total_sum += product_sum(ele, depth + 1) if isinstance(ele, list) else ele
    return total_sum * depth
