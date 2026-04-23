def advanced_split(splitted_string, spliter, include_spliter=False):
    splitted_string_tmp = []
    for string_ in splitted_string:
        if spliter in string_:
            splitted = string_.split(spliter)
            for i, s in enumerate(splitted):
                if include_spliter:
                    if i != len(splitted)-1:
                        splitted[i] += spliter
                splitted[i] = splitted[i].strip()
            for i in reversed(range(len(splitted))):
                if not contains_chinese(splitted[i]):
                    splitted.pop(i)
            splitted_string_tmp.extend(splitted)
        else:
            splitted_string_tmp.append(string_)
    splitted_string = splitted_string_tmp
    return splitted_string_tmp