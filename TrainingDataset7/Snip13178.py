def split_contents(self):
        split = []
        bits = smart_split(self.contents)
        for bit in bits:
            # Handle translation-marked template pieces
            if bit.startswith(('_("', "_('")):
                sentinel = bit[2] + ")"
                trans_bit = [bit]
                while not bit.endswith(sentinel):
                    bit = next(bits)
                    trans_bit.append(bit)
                bit = " ".join(trans_bit)
            split.append(bit)
        return split