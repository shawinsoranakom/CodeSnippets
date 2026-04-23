def delta_path(self) -> List[int]:
        """The complete path of the delta pointed to by this cursor - its
        container, parent path, and index.
        """
        return make_delta_path(self.root_container, self.parent_path, self.index)