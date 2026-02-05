def delete(self, word: str) -> None:

    def _delete(curr: TrieNode, word: str, index: int) -> bool:
        if index == len(word):
            if not curr.is_leaf:
                return False
            curr.is_leaf = False
            return len(curr.nodes) == 0
        char = word[index]
        char_node = curr.nodes.get(char)
        if not char_node:
            return False
        delete_curr = _delete(char_node, word, index + 1)
        if delete_curr:
            del curr.nodes[char]
            return len(curr.nodes) == 0
        return delete_curr

    _delete(self, word, 0)
