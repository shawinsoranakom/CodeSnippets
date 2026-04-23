def dp_knapsack_sliding_hirschberg(
    memory: list[float], runtime: list[float], max_memory: float
) -> tuple[float, list[int], list[int]]:
    # Scaling factor to convert floating point weights to integers
    S = 10000

    # q_ prefix stands for quantized
    q_memory = [int(round(m * S)) for m in memory]
    runtimes = [float(v) for v in runtime]

    q_max_memory = int(round(max_memory * S))

    q_memory_length = len(q_memory)
    if q_memory_length == 0:
        return 0.0, [], []

    item_indices = list(range(q_memory_length))
    dp_profile_size = q_max_memory + 1

    # Current DP profile (row)
    dp_profile = torch.zeros(dp_profile_size, dtype=torch.float32, device="cpu")
    # Store a candidate for next dp_profile - current dp row + item
    candidate_profile = torch.empty(dp_profile_size, dtype=torch.float32, device="cpu")
    left_profile = torch.empty(dp_profile_size, dtype=torch.float32, device="cpu")
    right_profile = torch.empty(dp_profile_size, dtype=torch.float32, device="cpu")

    saved_items: list[int] = []
    recomputable_items: list[int] = []

    # Explicit stack to optimize memory and avoid recursion
    # Stack stores segments as (start index, end index, capacity for segment)
    stack: list[tuple[int, int, int]] = [(0, q_memory_length, q_max_memory)]

    # LIFO
    while stack:
        start, end, capacity = stack.pop()
        length = end - start
        if length == 0:
            continue

        # Leaf
        if length == 1:
            index = item_indices[start]
            memory_item = q_memory[index]
            runtime_item = runtimes[index]
            if memory_item <= capacity and runtime_item > 0.0:
                saved_items.append(index)
            else:
                recomputable_items.append(index)
            continue

        # Split the segment into two halves
        middle = start + (length // 2)
        left_start, left_end = middle, end
        right_start, right_end = start, middle

        # Assign items to both halves
        left_items = item_indices[left_start:left_end]
        right_items = item_indices[right_start:right_end]

        # Working only on items allowed by segment's capacity
        capacity = capacity + 1
        dp_view = dp_profile[:capacity]
        candidate_view = candidate_profile[:capacity]
        left_dp_local = left_profile[:capacity]
        right_dp_local = right_profile[:capacity]

        # Left part
        dp_view.zero_()
        for index in left_items:
            memory_item = q_memory[index]
            runtime_item = runtimes[index]

            if memory_item == 0:
                # Weight is 0, so add it to all capacities; a "free lunch", essentially
                dp_view.add_(runtime_item)
                continue

            # If item is too heavy, we skip it
            if memory_item >= capacity:
                continue

            # Add the current item so we can then pick the highest value
            dp_view_candidate = candidate_view[: capacity - memory_item]
            torch.add(dp_view[:-memory_item], runtime_item, out=dp_view_candidate)
            # Take the highest - either previous (without current) or with current
            torch.maximum(
                dp_view[memory_item:], dp_view_candidate, out=dp_view[memory_item:]
            )

        # Store the left profile
        left_dp_local.copy_(dp_view)

        # Right part
        dp_view.zero_()
        for index in right_items:
            memory_item = q_memory[index]
            runtime_item = runtimes[index]

            if memory_item == 0:
                dp_view.add_(runtime_item)
                continue

            if memory_item >= capacity:
                continue

            dp_view_candidate = candidate_view[: capacity - memory_item]
            torch.add(dp_view[:-memory_item], runtime_item, out=dp_view_candidate)
            torch.maximum(
                dp_view[memory_item:], dp_view_candidate, out=dp_view[memory_item:]
            )

        # Store the reversed right profile
        right_dp_local.copy_(dp_view.flip(-1))

        # In-place compute item-wise sum of left and right to pick the split point where the sum is highest
        left_dp_local.add_(right_dp_local)

        # Pick the index of highest value of a pair, which we then use as a split point
        best_split = int(torch.argmax(left_dp_local).item())

        left_capacity = best_split
        right_capacity = capacity - best_split

        # Clamp (might be removed if we're 100% sure that there is no edge case that will mess up the indices math)
        if left_capacity < 0:
            left_capacity = 0
        if right_capacity < 0:
            right_capacity = 0
        if left_capacity > q_max_memory:
            left_capacity = q_max_memory
        if right_capacity > q_max_memory:
            right_capacity = q_max_memory

        # Push right then left, so left is processed next
        stack.append((right_start, right_end, right_capacity))
        stack.append((left_start, left_end, left_capacity))

    saved_items = sorted(saved_items)
    recomputable_items = sorted(recomputable_items)

    max_runtime = sum(runtime[i] for i in saved_items)
    recomputable_items.reverse()
    return max_runtime, saved_items, recomputable_items