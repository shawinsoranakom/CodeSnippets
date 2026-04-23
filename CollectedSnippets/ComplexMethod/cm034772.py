def lzw_compress(data: Optional[str], bits: int, char_func: Callable[[int], str]) -> str:
    if data is None:
        return ""

    dictionary: Dict[str, int] = {}
    dict_to_create: Dict[str, bool] = {}

    c = ""
    wc = ""
    w = ""

    enlarge_in = 2
    dict_size = 3
    num_bits = 2

    result: List[str] = []
    value = 0
    position = 0

    for i in range(len(data)):
        c = data[i]

        if c not in dictionary:
            dictionary[c] = dict_size
            dict_size += 1
            dict_to_create[c] = True

        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            if w in dict_to_create:
                # output "w" as a raw char (8-bit or 16-bit)
                if ord(w[0]) < 256:
                    # write num_bits zeros
                    for _ in range(num_bits):
                        value = (value << 1)
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1

                    char_code = ord(w[0])
                    for _ in range(8):
                        value = (value << 1) | (char_code & 1)
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1
                        char_code >>= 1
                else:
                    # write a 1 marker
                    char_code = 1
                    for _ in range(num_bits):
                        value = (value << 1) | char_code
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1
                        char_code = 0

                    char_code = ord(w[0])
                    for _ in range(16):
                        value = (value << 1) | (char_code & 1)
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1
                        char_code >>= 1

                enlarge_in -= 1
                if enlarge_in == 0:
                    enlarge_in = 2 ** num_bits
                    num_bits += 1

                del dict_to_create[w]
            else:
                # output dictionary code for w
                char_code = dictionary[w]
                for _ in range(num_bits):
                    value = (value << 1) | (char_code & 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code >>= 1

            enlarge_in -= 1
            if enlarge_in == 0:
                enlarge_in = 2 ** num_bits
                num_bits += 1

            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    # flush remaining w
    if w != "":
        if w in dict_to_create:
            if ord(w[0]) < 256:
                for _ in range(num_bits):
                    value = (value << 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1

                char_code = ord(w[0])
                for _ in range(8):
                    value = (value << 1) | (char_code & 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code >>= 1
            else:
                char_code = 1
                for _ in range(num_bits):
                    value = (value << 1) | char_code
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code = 0

                char_code = ord(w[0])
                for _ in range(16):
                    value = (value << 1) | (char_code & 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code >>= 1

            enlarge_in -= 1
            if enlarge_in == 0:
                enlarge_in = 2 ** num_bits
                num_bits += 1
            del dict_to_create[w]
        else:
            char_code = dictionary[w]
            for _ in range(num_bits):
                value = (value << 1) | (char_code & 1)
                if position == bits - 1:
                    position = 0
                    result.append(char_func(value))
                    value = 0
                else:
                    position += 1
                char_code >>= 1

        enlarge_in -= 1
        if enlarge_in == 0:
            enlarge_in = 2 ** num_bits
            num_bits += 1

    # end-of-stream marker (2)
    char_code = 2
    for _ in range(num_bits):
        value = (value << 1) | (char_code & 1)
        if position == bits - 1:
            position = 0
            result.append(char_func(value))
            value = 0
        else:
            position += 1
        char_code >>= 1

    # pad to complete a char
    while True:
        value = (value << 1)
        if position == bits - 1:
            result.append(char_func(value))
            break
        position += 1

    return "".join(result)