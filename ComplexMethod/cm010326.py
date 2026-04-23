def run_from(self, node_idx):
        module_idx = 0
        # Walk through the graph, building up a new graph with the right submodules
        while node_idx < len(self.nodes):
            node = self.nodes[node_idx]
            if node.op == "placeholder":
                raise AssertionError(f"unexpected placeholder node at index {node_idx}")

            self.print()
            self.print("STEP", node_idx, node.format_node())
            self.print(self.module_stack)
            depth = len(self.module_stack)
            if node.op == "output":
                if depth == 1:
                    # We want the output node of the original graph to be handled
                    # specially by the outermost stack frame (in run_outer). So
                    # skip finalization here.
                    return node_idx

                # We've reached the end of the graph. Wrap up all the existing stack frames.
                self.finalize_outputs()
                return node_idx

            if len(node.meta.get("nn_module_stack", {})) == 0:
                raise RuntimeError(f"Unable to find nn_module_stack for node {node}")

            nn_module_stack = node.meta["nn_module_stack"]
            from torch._export.passes._node_metadata_hook import (
                _EMPTY_NN_MODULE_STACK_KEY,
            )

            if (
                len(nn_module_stack) == 1
                and _EMPTY_NN_MODULE_STACK_KEY in nn_module_stack
            ):
                # Empty case from the node_metadata_hook
                node_module_stack = self.module_stack
            else:
                node_module_stack = [
                    (
                        path,
                        ty if path else None,
                        int(k.split("@")[-1]) if "@" in k else 0,
                    )
                    for k, (path, ty) in node.meta["nn_module_stack"].items()
                ]

            if node_module_stack[:depth] != self.module_stack:
                # This means that the current module is done executing and the
                # current node is the beginning of a new module.
                #
                # In this case, we should finalize this module and return without
                # incrementing the node counter.
                self.finalize_outputs()
                self.print("outlining", self.fqn)
                self.print(self.graph)
                return node_idx

            if node_module_stack is None:
                raise AssertionError("node_module_stack must not be None")

            if _is_prefix(self.module_stack, node_module_stack):
                # This means that the current node represents the execution of a new
                # module.
                next_module = node_module_stack[depth]
                self.print("Creating new stack frame for", next_module)
                # Run a nested version of module outliner from the current node
                # counter. Once it is complete, continue from that point.
                next_module_key = list(node.meta["nn_module_stack"].keys())[depth]
                node_idx = _ModuleFrame(
                    self.flat_graph,
                    self.nodes,
                    self.seen_nodes,
                    self.seen_modules,
                    self.seen_attrs,
                    self.created_modules,
                    self,
                    self.module_stack + [next_module],
                    next_module_key.split("@")[0],
                    self.module_call_graph,
                ).run_from(node_idx)
                module_idx += 1
                continue

            # The only remaining possibility is that we are in the right stack
            # frame. Copy the node into this frame's graph and increment the node counter.
            if node_module_stack != self.module_stack:
                raise AssertionError(
                    f"expected node_module_stack {node_module_stack} to equal module_stack {self.module_stack}"
                )

            if node.op == "get_attr":
                # this must be a graph argument for a HOP
                self.seen_attrs[self.child_fqn].add(node.target)

            self.copy_node(node)
            # pyrefly: ignore [unsupported-operation]
            node_idx += 1