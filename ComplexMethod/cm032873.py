def binary_search(arr, target):
        if not arr:
            return -1
        if target > arr[-1]:
            return len(arr) - 1
        if target < arr[0]:
            return -1
        s, e = 0, len(arr)
        while e - s > 1:
            i = (e + s) // 2
            if target > arr[i]:
                s = i
                continue
            elif target < arr[i]:
                e = i
                continue
            else:
                assert False
        return s