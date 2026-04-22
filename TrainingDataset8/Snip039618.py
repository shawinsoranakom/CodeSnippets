def side_effect(i):
            if i == 123456789:
                return "a" + 1
            return i.to_bytes((i.bit_length() + 8) // 8, "little", signed=True)