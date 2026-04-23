def find_missing_number(nums: list[int]) -> int:

    low = min(nums)
    high = max(nums)
    missing_number = high

    for i in range(low, high):
        missing_number ^= i ^ nums[i - low]

    return missing_number
