def convert_id_to_token(self, index, breakline="\n"):
        words = []
        byte_tokens = []
        word = self.ids_to_tokens[index][0]
        if word[:6] == "<|byte" and word[-2:] == "|>":
            byte_tokens.append(int(word[6:-2]))
        else:
            if len(byte_tokens) > 0:
                words.append(bytearray(byte_tokens).decode("utf-8", errors="replace"))
                byte_tokens = []
            if word[:7] == "<|emoji" and word[-2:] == "|>":
                words.append(self.emoji["emoji_inv"][word])
            elif word == "<SP>":
                words.append(" ")
            elif word == "<BR>":
                words.append(breakline)
            elif word == "<TAB>":
                words.append("\t")
            elif word == "<BLOCK>":
                words.append("▀")
            elif word == "<KIGOU>":
                words.append("ǀ")
            elif word == "<U2000U2BFF>":
                words.append("‖")
            else:
                words.append(word)
        if len(byte_tokens) > 0:
            words.append(bytearray(byte_tokens).decode("utf-8", errors="replace"))
        text = "".join(words)
        return text