def helper(treespec: PyTreeSpec) -> str:
            if treespec.is_leaf():
                assert treespec.type is None
                return _asterisk

            assert treespec.type is not None
            assert callable(treespec._unflatten_func)
            children_representations = [
                helper(subspec) for subspec in treespec._children
            ]
            if (
                treespec.type in BUILTIN_TYPES
                or (treespec.type is type(None) and not self.none_is_leaf)
                or optree.is_namedtuple_class(treespec.type)
                or optree.is_structseq_class(treespec.type)
            ):
                return treespec._unflatten_func(
                    treespec._metadata,
                    children_representations,
                )
            return (
                f"CustomTreeNode({treespec.type.__name__}[{treespec._metadata!r}], "
                f"[{', '.join(children_representations)}])"
            )