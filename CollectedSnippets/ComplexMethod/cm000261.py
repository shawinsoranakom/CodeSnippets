def delete(self, word: str) -> bool:
        """Deletes a word from the tree if it exists

        Args:
            word (str): word to be deleted

        Returns:
            bool: True if the word was found and deleted. False if word is not found

        >>> RadixNode("myprefix").delete("mystring")
        False
        """
        incoming_node = self.nodes.get(word[0], None)
        if not incoming_node:
            return False
        else:
            _matching_string, remaining_prefix, remaining_word = incoming_node.match(
                word
            )
            # If there is remaining prefix, the word can't be on the tree
            if remaining_prefix != "":
                return False
            # We have word remaining so we check the next node
            elif remaining_word != "":
                return incoming_node.delete(remaining_word)
            # If it is not a leaf, we don't have to delete
            elif not incoming_node.is_leaf:
                return False
            else:
                # We delete the nodes if no edges go from it
                if len(incoming_node.nodes) == 0:
                    del self.nodes[word[0]]
                    # We merge the current node with its only child
                    if len(self.nodes) == 1 and not self.is_leaf:
                        merging_node = next(iter(self.nodes.values()))
                        self.is_leaf = merging_node.is_leaf
                        self.prefix += merging_node.prefix
                        self.nodes = merging_node.nodes
                # If there is more than 1 edge, we just mark it as non-leaf
                elif len(incoming_node.nodes) > 1:
                    incoming_node.is_leaf = False
                # If there is 1 edge, we merge it with its child
                else:
                    merging_node = next(iter(incoming_node.nodes.values()))
                    incoming_node.is_leaf = merging_node.is_leaf
                    incoming_node.prefix += merging_node.prefix
                    incoming_node.nodes = merging_node.nodes

                return True