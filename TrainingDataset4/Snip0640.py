def find(self, word: str) -> bool:
    incoming_node = self.nodes.get(word[0], None)
    if not incoming_node:
        return False
    else:
        _matching_string, remaining_prefix, remaining_word = incoming_node.match(
            word
        )
        if remaining_prefix != "":
            return False
        elif remaining_word == "":
            return incoming_node.is_leaf
        else:
            return incoming_node.find(remaining_word)
