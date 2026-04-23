def test_annotate_getitem_node(self):
        class CustomType:
            pass

        class CustomNamedTuple(NamedTuple):
            x: int
            y: float

        class MyModule(torch.nn.Module):
            def forward(self, inp: tuple[CustomType, torch.Tensor], inp2: list[CustomType], inp3: CustomNamedTuple):
                inp_0 = inp[0]
                inp_1 = inp[1]
                inp2_0 = inp2[0]
                inp3_x = inp3.x
                inp3_y = inp3.y
                return inp_0 + inp_1 + inp2_0 + inp3_x + inp3_y

        class MyModule2(torch.nn.Module):
            def forward(self, inp: tuple[CustomType, torch.Tensor], inp2: list[CustomType], inp3: CustomNamedTuple):
                inp_0 = inp[0]
                inp_1 = inp[1]
                inp2_0 = inp2[0]
                inp3_x = inp3.x
                inp3_y = inp3.y
                return inp_0 + inp_1 + inp2_0 + inp3_x + inp3_y

        my_module = MyModule()
        my_module_traced = torch.fx.symbolic_trace(my_module)

        # by default, fx transform loses type annotation of getitem nodes.
        for node in my_module_traced.graph.nodes:
            if node.target == operator.getitem:
                if node.type is not None:
                    raise AssertionError(f"expected node.type is None, got {node.type}")

        annotate_getitem_nodes(my_module_traced.graph)

        for node in my_module_traced.graph.nodes:
            if node.target == operator.getitem:
                self.assertIsNotNone(node.type, f"Node {node} should be annotated but is not.")

        my_module = MyModule2()
        my_module_traced = torch.fx.symbolic_trace(my_module)

        # by default, fx transform loses type annotation of getitem nodes.
        for node in my_module_traced.graph.nodes:
            if node.target == operator.getitem:
                if node.type is not None:
                    raise AssertionError(f"expected node.type is None, got {node.type}")

        annotate_getitem_nodes(my_module_traced.graph)

        for node in my_module_traced.graph.nodes:
            if node.target == operator.getitem:
                self.assertIsNotNone(node.type, f"Node {node} should be annotated but is not.")