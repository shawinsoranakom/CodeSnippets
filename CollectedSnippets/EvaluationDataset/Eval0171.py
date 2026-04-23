def permute_backtrack(nums: list[int]) -> list[list[int]]:

    def backtrack(start: int) -> None:
        if start == len(nums) - 1:
            output.append(nums[:])
        else:
            for i in range(start, len(nums)):
                nums[start], nums[i] = nums[i], nums[start]
                backtrack(start + 1)
                nums[start], nums[i] = nums[i], nums[start]  

    output: list[list[int]] = []
    backtrack(0)
    return output
