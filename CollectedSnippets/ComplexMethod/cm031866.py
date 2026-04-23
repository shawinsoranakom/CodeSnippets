def insert(self, word, value):
        if not all(0 <= ord(c) < 128 for c in word):
            raise ValueError("Use 7-bit ASCII characters only")
        if word <= self.previous_word:
            raise ValueError("Error: Words must be inserted in alphabetical order.")
        if value in self.inverse:
            raise ValueError(f"value {value} is duplicate, got it for word {self.inverse[value]} and now {word}")

        # find common prefix between word and previous word
        common_prefix = 0
        for i in range(min(len(word), len(self.previous_word))):
            if word[i] != self.previous_word[i]:
                break
            common_prefix += 1

        # Check the unchecked_nodes for redundant nodes, proceeding from last
        # one down to the common prefix size. Then truncate the list at that
        # point.
        self._minimize(common_prefix)

        self.data[word] = value
        self.inverse[value] = word

        # add the suffix, starting from the correct node mid-way through the
        # graph
        if len(self.unchecked_nodes) == 0:
            node = self.root
        else:
            node = self.unchecked_nodes[-1][2]

        for letter in word[common_prefix:]:
            next_node = DawgNode(self)
            node.edges[letter] = next_node
            self.unchecked_nodes.append((node, letter, next_node))
            node = next_node

        node.final = True
        self.previous_word = word