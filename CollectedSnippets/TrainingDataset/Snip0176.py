def decimal_to_binary(no_of_variable: int, minterms: Sequence[float]) -> list[str]:
   
    temp = []
    for minterm in minterms:
        string = ""
        for _ in range(no_of_variable):
            string = str(minterm % 2) + string
            minterm //= 2
        temp.append(string)
    return temp

