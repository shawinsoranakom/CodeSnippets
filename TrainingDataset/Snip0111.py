def generate_sum_of_subsets_solutions(nums: list[int], max_sum: int) -> list[list[int]]:

    result: list[list[int]] = []
    path: list[int] = []
    num_index = 0
    remaining_nums_sum = sum(nums)
    create_state_space_tree(nums, max_sum, num_index, path, result, remaining_nums_sum)
    return result
