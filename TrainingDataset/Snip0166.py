def mmain() -> None:
   
    kmap = [[0, 1], [1, 1]]


    for row in kmap:
        print(row)

    print("Simplified Expression:")
    print(simplify_kmap(kmap))
