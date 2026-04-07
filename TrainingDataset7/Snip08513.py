def resolve(self, path, create_if_missing=False, leaf_cls=None, check_exists=True):
        """
        Navigate current directory tree, returning node matching path or
        creating a new one, if missing.
        - path: path of the node to search
        - create_if_missing: create nodes if not exist. Defaults to False.
        - leaf_cls: expected type of leaf node. Defaults to None.
        - check_exists: if True and the leaf node does not exist, raise a
          FileNotFoundError. Defaults to True.
        """
        path_segments = list(pathlib.Path(path).parts)
        current_node = self

        while path_segments:
            path_segment = path_segments.pop(0)
            # If current node is a file node and there are unprocessed
            # segments, raise an error.
            if isinstance(current_node, InMemoryFileNode):
                path_segments = os.path.split(path)
                current_path = "/".join(
                    path_segments[: path_segments.index(path_segment)]
                )
                raise NotADirectoryError(
                    errno.ENOTDIR, os.strerror(errno.ENOTDIR), current_path
                )
            current_node = current_node._resolve_child(
                path_segment,
                create_if_missing,
                leaf_cls if len(path_segments) == 0 else InMemoryDirNode,
            )
            if current_node is None:
                break

        if current_node is None and check_exists:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

        # If a leaf_cls is not None, check if leaf node is of right type.
        if leaf_cls and not isinstance(current_node, leaf_cls):
            error_cls, error_code = (
                (NotADirectoryError, errno.ENOTDIR)
                if leaf_cls is InMemoryDirNode
                else (IsADirectoryError, errno.EISDIR)
            )
            raise error_cls(error_code, os.strerror(error_code), path)

        return current_node