def insert(self, word: str) -> None:
    if self.prefix == word and not self.is_leaf:
        self.is_leaf = True
    elif word[0] not in self.nodes:
        self.nodes[word[0]] = RadixNode(prefix=word, is_leaf=True)

    else:
        incoming_node = self.nodes[word[0]]
        matching_string, remaining_prefix, remaining_word = incoming_node.match(
            word
        )
        if remaining_prefix == "":
            self.nodes[matching_string[0]].insert(remaining_word)
        else:
            incoming_node.prefix = remaining_prefix

            aux_node = self.nodes[matching_string[0]]
            self.nodes[matching_string[0]] = RadixNode(matching_string, False)
            self.nodes[matching_string[0]].nodes[remaining_prefix[0]] = aux_node

            if remaining_word == "":
                self.nodes[matching_string[0]].is_leaf = True
            else:
                self.nodes[matching_string[0]].insert(remaining_word)
