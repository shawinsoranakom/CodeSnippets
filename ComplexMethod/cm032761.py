def _dfs(self, chunk_paths, titles, depth, include_heading_content):
        if self.level == 0 and self.body_indexes:
            chunk_paths.append(titles + self.body_indexes)

        if include_heading_content:
            path_titles = titles + self.title_indexes if 1 <= self.level <= depth else titles

            if self.body_indexes and 1 <= self.level <= depth:
                chunk_paths.append(path_titles + self.body_indexes)
            elif not self.children and 1 <= self.level <= depth:
                chunk_paths.append(path_titles)
        else:
            path_titles = (
                titles + self.title_indexes + self.body_indexes
                if 1 <= self.level <= depth
                else titles
            )

            if not self.children and 1 <= self.level <= depth:
                chunk_paths.append(path_titles)

        for child in self.children:
            child._dfs(chunk_paths, path_titles, depth, include_heading_content)