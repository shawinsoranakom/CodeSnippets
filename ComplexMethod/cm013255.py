def get_nodes_and_parents_recursively(block, kind, acc):
            for node in block.nodes():
                if node.kind() == kind:
                    acc[block].append(node)
                elif node.kind() == 'prim::DifferentiableGraph':
                    get_nodes_and_parents_recursively(node.g('Subgraph'), kind, acc)
                elif node.kind() == 'prim::If' and (node.inputs().__next__().node().kind() == 'aten::all' or
                                                    node.inputs().__next__().node().kind() == 'prim::TypeCheck' or
                                                    node.inputs().__next__().node().kind() == 'prim::RequiresGradCheck'):
                    get_nodes_and_parents_recursively(node.blocks().__next__(), kind, acc)
                else:
                    for inner_block in node.blocks():
                        get_nodes_and_parents_recursively(inner_block, kind, acc)