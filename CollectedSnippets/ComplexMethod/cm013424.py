def delete_all_unused_submodules(self) -> None:
        """
        Deletes all unused submodules from ``self``.

        A Module is considered "used" if any one of the following is
        true:
        1. It has children that are used
        2. Its forward is called directly via a ``call_module`` node
        3. It has a non-Module attribute that is used from a
        ``get_attr`` node

        This method can be called to clean up an ``nn.Module`` without
        manually calling ``delete_submodule`` on each unused submodule.
        """
        used: list[str] = []

        for node in self.graph.nodes:
            if node.op in ("call_module", "get_attr") and isinstance(node.target, str):
                # A list of strings representing the different parts
                # of the path. For example, `foo.bar.baz` gives us
                # ["foo", "bar", "baz"]
                fullpath = node.target.split(".")

                # If we're looking at multiple parts of a path, join
                # join them with a dot. Otherwise, return that single
                # element without doing anything to it.
                def join_fn(x: str, y: str) -> str:
                    return ".".join([x, y] if y else [x])

                # Progressively collect all the names of intermediate
                # modules. For example, if we have the target
                # `foo.bar.baz`, we'll add `foo`, `foo.bar`, and
                # `foo.bar.baz` to the list.
                used.extend(itertools.accumulate(fullpath, join_fn))

                # For a `call_module` node, also register all recursive submodules
                # as used
                if node.op == "call_module":
                    try:
                        str_target = cast(str, node.target)
                        submod = self.get_submodule(str_target)

                        for submod_name, _ in submod.named_modules():
                            if submod_name != "":
                                used.append(".".join([str_target, submod_name]))
                    except AttributeError:
                        # Node referenced nonexistent submodule, don't need to
                        # worry about GCing anything
                        pass

        to_delete = [name for name, _ in self.named_modules() if name not in used]

        for name in to_delete:
            self.delete_submodule(name)