def delete(self, word: str) -> bool:
    incoming_node = self.nodes.get(word[0], None)
    if not incoming_node:
        return False
    else:
        _matching_string, remaining_prefix, remaining_word = incoming_node.match(
            word
        )
        if remaining_prefix != "":
            return False
        elif remaining_word != "":
            return incoming_node.delete(remaining_word)
        elif not incoming_node.is_leaf:
            return False
        else:
            if len(incoming_node.nodes) == 0:
                del self.nodes[word[0]]
                if len(self.nodes) == 1 and not self.is_leaf:
                    merging_node = next(iter(self.nodes.values()))
                    self.is_leaf = merging_node.is_leaf
                    self.prefix += merging_node.prefix
                    self.nodes = merging_node.nodes
            elif len(incoming_node.nodes) > 1:
                incoming_node.is_leaf = False
            else:
                merging_node = next(iter(incoming_node.nodes.values()))
                incoming_node.is_leaf = merging_node.is_leaf
                incoming_node.prefix += merging_node.prefix
                incoming_node.nodes = merging_node.nodes

            return True
