def _dfs(self, node, tree_list, titles):
        level = node.get_level()
        texts = node.get_texts()
        child = node.get_children()

        if level == 0 and texts:
            tree_list.append("\n".join(titles + texts))

        # Titles within configured depth are accumulated into the current path
        if 1 <= level <= self.depth:
            path_titles = titles + texts
        else:
            path_titles = titles

        # Body outside the depth limit becomes its own chunk under the current title path
        if level > self.depth and texts:
            tree_list.append("\n".join(path_titles + texts))

        # A leaf title within depth emits its title path as a chunk (header-only section)
        elif not child and (1 <= level <= self.depth):
            tree_list.append("\n".join(path_titles))

        # Recurse into children with the updated title path
        for c in child:
            self._dfs(c, tree_list, path_titles)