def check_orig_and_eq_graphs(self, orig_model, eq_model):
        """ Given a non-equalized model and an equalized model, check that the
        graphs are structured in the same way, except the equalized model has
        additional 'equalization_scale' and 'mul' nodes.
        """
        orig_idx = 0
        orig_nodes = list(orig_model.graph.nodes)
        orig_modules = dict(orig_model.named_modules(remove_duplicate=False))

        eq_idx = 0
        eq_nodes = list(eq_model.graph.nodes)
        eq_modules = dict(eq_model.named_modules(remove_duplicate=False))

        while orig_idx < len(orig_nodes) and eq_idx < len(eq_nodes):
            if 'equalization_scale' in eq_nodes[eq_idx].name and 'mul' in eq_nodes[eq_idx + 1].name:
                # Skip the equalization and mul nodes
                eq_idx += 2
                continue
            elif orig_nodes[orig_idx].op != eq_nodes[eq_idx].op:
                return False
            elif orig_nodes[orig_idx].op == 'call_module':
                # Check that the type of call_modules are the same (ex. nn.Linear, MinMaxObserver)
                orig_node = orig_nodes[orig_idx]
                eq_node = eq_nodes[eq_idx]
                if type(orig_modules[orig_node.target]) is not type(eq_modules[eq_node.target]):
                    return False
            elif orig_nodes[orig_idx].op == 'call_function':
                # Check that the call_functions are the same (ex. F.linear)
                orig_node = orig_nodes[orig_idx]
                eq_node = eq_nodes[eq_idx]
                if orig_node.target != eq_node.target:
                    return False

            eq_idx += 1
            orig_idx += 1

        return True