def circle_sort_util(collection: list, low: int, high: int) -> bool:
        """
        >>> arr = [5,4,3,2,1]
        >>> circle_sort_util(lst, 0, 2)
        True
        >>> arr
        [3, 4, 5, 2, 1]
        """

        swapped = False

        if low == high:
            return swapped

        left = low
        right = high

        while left < right:
            if collection[left] > collection[right]:
                collection[left], collection[right] = (
                    collection[right],
                    collection[left],
                )
                swapped = True

            left += 1
            right -= 1

        if left == right and collection[left] > collection[right + 1]:
            collection[left], collection[right + 1] = (
                collection[right + 1],
                collection[left],
            )

            swapped = True

        mid = low + int((high - low) / 2)
        left_swap = circle_sort_util(collection, low, mid)
        right_swap = circle_sort_util(collection, mid + 1, high)

        return swapped or left_swap or right_swap