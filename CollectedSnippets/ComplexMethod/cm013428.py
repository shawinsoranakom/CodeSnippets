def replace_all_uses_with(
        self,
        replace_with: "Node",
        delete_user_cb: Callable[["Node"], bool] | None = None,
        *,
        propagate_meta: bool = False,
    ) -> list["Node"]:
        """
        Replace all uses of ``self`` in the Graph with the Node ``replace_with``.

        Args:

            replace_with (Node): The node to replace all uses of ``self`` with.
            delete_user_cb (Callable): Callback that is called to determine
              whether a given user of the self node should be removed.
            propagate_meta (bool): Whether or not to copy all properties
              on the .meta field of the original node onto the replacement node.
              For safety, this is only valid to do if the replacement node
              doesn't already have an existing .meta field.

        Returns:

            The list of Nodes on which this change was made.
        """
        if propagate_meta:
            if len(replace_with.meta) != 0:
                raise AssertionError(
                    "Called node.replace_all_uses_with(replace_with, propagate_meta=True), "
                    "but replace_with already has .meta keys"
                )
            for k, v in self.meta.items():
                replace_with.meta[k] = v
        to_process = [*self.users]
        replace_hooks = getattr(self.graph.owning_module, "_replace_hooks", None)
        result = []
        for use_node in to_process:
            if delete_user_cb is not None and not delete_user_cb(use_node):
                continue
            result.append(use_node)
            if replace_hooks:
                for replace_hook in replace_hooks:
                    replace_hook(old=self, new=replace_with.name, user=use_node)

            use_node._replace_input_with(self, replace_with)
        return result