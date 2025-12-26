def find_triplets_with_0_sum_hashing(arr: list[int]) -> list[list[int]]:

    target_sum = 0

    output_arr = []

    for index, item in enumerate(arr[:-2]):
        set_initialize = set()

        current_sum = target_sum - item

        for other_item in arr[index + 1 :]:
            required_value = current_sum - other_item

            if required_value in set_initialize:
                combination_array = sorted([item, other_item, required_value])
                if combination_array not in output_arr:
                    output_arr.append(combination_array)

            set_initialize.add(other_item)

    return output_arr

