def _compare(
                treespec: TreeSpec, other_treespec: TreeSpec, path: KeyPath
            ) -> None:
                # raise an error at the point where tree and dynamic_shapes differ,
                # including the path to that point and the reason for the difference
                rendered_path = keystr(path)
                if treespec.is_leaf():
                    return
                if other_treespec.is_leaf():
                    raise_mismatch_error(
                        f"`{tree_name}{rendered_path}` is a {treespec.type}, "
                        f"but `dynamic_shapes{rendered_path}` is not"
                    )
                if treespec.type != other_treespec.type:
                    raise_mismatch_error(
                        f"`{tree_name}{rendered_path}` is a {treespec.type}, "
                        f"but `dynamic_shapes{rendered_path}` is a {other_treespec.type}"
                    )
                if treespec.num_children != other_treespec.num_children:
                    raise_mismatch_error(
                        f"`{tree_name}{rendered_path}` has {treespec.num_children} elements, "
                        f"but `dynamic_shapes{rendered_path}` has {other_treespec.num_children} elements"
                    )
                if treespec.type is dict:
                    # context, children could be out of order
                    if set(treespec.context) != set(other_treespec.context):
                        raise_mismatch_error(
                            f"`{tree_name}{rendered_path}` has keys {treespec.context}, "
                            f"but `dynamic_shapes{rendered_path}` has keys {other_treespec.context}"
                        )
                    _remap = dict(
                        zip(other_treespec.context, other_treespec.children())
                    )
                    other_children = [_remap[k] for k in treespec.context]
                else:
                    other_children = other_treespec.children()
                for i, (child, other_child) in enumerate(
                    zip(treespec.children(), other_children)
                ):
                    _compare(
                        child,
                        other_child,
                        path + (_key(treespec.type, treespec.context, i),),
                    )