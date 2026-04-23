def generate(k: int, arr: list):
    if k == 1:
        res.append(tuple(arr[:]))
        return

    generate(k - 1, arr)

    for i in range(k - 1):
        if k % 2 == 0: 
            arr[i], arr[k - 1] = arr[k - 1], arr[i]
        else:  
            arr[0], arr[k - 1] = arr[k - 1], arr[0]
        generate(k - 1, arr)
