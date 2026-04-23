def encode(self, text):
        """ """
        if len(text) == 0 or len(text) > self.max_text_len:
            return None, None, None
        if self.lower:
            text = text.lower()
        text_node = [0 for _ in range(self.num_character)]
        text_node[0] = 1
        text_list = []
        ch_order = []
        order = 1
        for char in text:
            if char not in self.dict:
                continue
            text_list.append(self.dict[char])
            text_node[self.dict[char]] += 1
            ch_order.append([self.dict[char], text_node[self.dict[char]], order])
            order += 1

        no_ch_order = []
        for char in self.character:
            if char not in text:
                no_ch_order.append([self.dict[char], 1, 0])
        random.shuffle(no_ch_order)
        ch_order = ch_order + no_ch_order
        ch_order = ch_order[: self.max_text_len + 1]

        if len(text_list) == 0:
            return None, None, None
        return text_list, text_node, ch_order.sort()