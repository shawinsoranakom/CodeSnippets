def check(binary: list[str]) -> list[str]:
    """
    >>> check(['0.00.01.5'])
    ['0.00.01.5']
    """
    pi = []
    while True:
        check1 = ["$"] * len(binary)
        temp = []
        for i in range(len(binary)):
            for j in range(i + 1, len(binary)):
                k = compare_string(binary[i], binary[j])
                if k is False:
                    check1[i] = "*"
                    check1[j] = "*"
                    temp.append("X")
        for i in range(len(binary)):
            if check1[i] == "$":
                pi.append(binary[i])
        if len(temp) == 0:
            return pi
        binary = list(set(temp))