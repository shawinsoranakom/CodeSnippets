def compare_string(string1: str, string2: str) -> str | Literal[False]:
    
    list1 = list(string1)
    list2 = list(string2)
    count = 0
    for i in range(len(list1)):
        if list1[i] != list2[i]:
            count += 1
            list1[i] = "_"
    if count > 1:
        return False
    else:
        return "".join(list1)
