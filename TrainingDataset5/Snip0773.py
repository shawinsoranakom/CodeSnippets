def maximum_non_adjacent_sum(nums: list[int]) -> int:
    if not nums:
        return 0
    max_including = nums[0]
    max_excluding = 0
    for num in nums[1:]:
        max_including, max_excluding = (
            max_excluding + num,
            max(max_including, max_excluding),
        )
    return max(max_excluding, max_including)
