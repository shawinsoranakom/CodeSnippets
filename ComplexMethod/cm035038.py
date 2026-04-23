def encodech(self, text):
        """ """
        if len(text) == 0 or len(text) > self.max_text_len:
            return None, None, None
        if self.lower:
            text = text.lower()
        text_node_dict = {}
        text_node_dict.update({0: 1})
        character_index = [_ for _ in range(self.num_character)]
        text_list = []
        for char in text:
            if char not in self.dict:
                continue
            i_c = self.dict[char]
            text_list.append(i_c)
            if i_c in text_node_dict.keys():
                text_node_dict[i_c] += 1
            else:
                text_node_dict.update({i_c: 1})
        for ic in list(text_node_dict.keys()):
            character_index.remove(ic)
        none_char_index = sample(character_index, 37 - len(list(text_node_dict.keys())))
        for ic in none_char_index:
            text_node_dict[ic] = 0

        text_node_index = sorted(text_node_dict)
        text_node_num = [text_node_dict[k] for k in text_node_index]
        if len(text_list) == 0:
            return None, None, None
        return text_list, text_node_index, text_node_num