def _pattern(self, root, digest):
        """Convert a Trie into a regular expression pattern

        Memoized on the hash digest of the trie, which is built incrementally
        during add().
        """
        node = root

        if "" in node.children and len(node.children.keys()) == 1:
            return None

        alt = []    # store alternative patterns
        cc = []     # store char to char classes
        q = 0       # for node representing the end of word
        for char in sorted(node.children.keys()):
            if isinstance(node.children[char], TrieNode):
                try:
                    recurse = self._pattern(node.children[char], self._digest)
                    alt.append(self.quote(char) + recurse)
                except Exception:
                    cc.append(self.quote(char))
            else:
                q = 1
        cconly = not len(alt) > 0

        if len(cc) > 0:
            if len(cc) == 1:
                alt.append(cc[0])
            else:
                alt.append('[' + ''.join(cc) + ']')

        if len(alt) == 1:
            result = alt[0]
        else:
            result = "(?:" + "|".join(alt) + ")"

        if q:
            if cconly:
                result += "?"
            else:
                result = f"(?:{result})?"
        return result