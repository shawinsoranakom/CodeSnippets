def test_tracing_graphmodules_as_leaf_submodules(self):
        class A(torch.nn.Module):
            def forward(self, t):
                return t + t

        class B(torch.nn.Module):
            def __init__(self) -> None:
                super(type(self), self).__init__()
                self.calling = False
                self.called = False

            def forward(self, t):
                if self.calling:
                    return t - t
                else:
                    return t + t

            def __call__(self, *args):
                self.called = True
                self.calling = True
                return super(type(self), self).__call__(*args)
                self.calling = False

        class M(torch.nn.Module):
            def __init__(self, a, b):
                super().__init__()
                self.a = a
                self.b = b

            def forward(self, t):
                x = self.a(t)
                y = self.b(t)
                return x + y

        class LeafTracer(Tracer):
            def is_leaf_module(self, module, name):
                return True

        class LeafTracerNotB(Tracer):
            def is_leaf_module(self, module, name):
                return "b" not in name

        # Recompile calls added "for fun", since they
        # chain __call__ wrappers.

        #
        # Test: B as a regular, non-leaf module
        #
        a = symbolic_trace(A())
        a.recompile()
        m = M(a, B())
        graph = LeafTracerNotB().trace(m)
        gm = GraphModule(m, graph)
        gm.recompile()

        # Test graphmodule/submodule a is not inlined.
        self.assertTrue(isinstance(gm.get_submodule("a"), GraphModule))
        match = [n for n in gm.graph.nodes if n.op == "call_module" and n.target == "a"]
        self.assertTrue(len(match) == 1)

        # Test submodule b is not treated as leaf.
        self.assertFalse(hasattr(gm, "b"))

        # Test assert custom __call__ on submodule b was honored.
        match = [
            n
            for n in gm.graph.nodes
            if n.op == "call_function" and n.target == operator.sub
        ]
        self.assertTrue(len(match) == 1)

        #
        # Test: B as a regular, leaf module
        # symbolic_trace should only patch torch.nn.Module.__call__,
        # which means B.__call__ should still execute
        #
        a = symbolic_trace(A())
        a.recompile()
        b = B()
        m = M(a, b)
        graph = LeafTracer().trace(m)
        gm = GraphModule(m, graph)
        gm.recompile()

        # Test graphmodule/submodule a is not inlined.
        self.assertTrue(isinstance(gm.get_submodule("a"), GraphModule))
        match = [n for n in gm.graph.nodes if n.op == "call_module" and n.target == "a"]
        self.assertTrue(len(match) == 1)

        # Test submodule b is leaf:
        self.assertTrue(isinstance(gm.get_submodule("b"), torch.nn.Module))
        match = [n for n in gm.graph.nodes if n.op == "call_module" and n.target == "b"]
        self.assertTrue(len(match) == 1)

        # Test b.__call__ was run
        self.assertTrue(b.called)
        self.assertTrue(gm.get_submodule("b").called)

        #
        # Test: B as GraphModule leaf
        # __call__ not honored since symbolic_trace directly invokes forward()
        #
        a = symbolic_trace(A())
        a.recompile()
        b = symbolic_trace(B())
        b.recompile()
        m = M(a, b)
        graph = LeafTracer().trace(m)
        gm = GraphModule(m, graph)
        gm.recompile()

        self.assertTrue(isinstance(gm.get_submodule("a"), GraphModule))
        match = [n for n in gm.graph.nodes if n.op == "call_module" and n.target == "a"]
        self.assertTrue(len(match) == 1)

        self.assertTrue(isinstance(gm.get_submodule("b"), torch.nn.Module))
        match = [n for n in gm.graph.nodes if n.op == "call_module" and n.target == "b"]
        self.assertTrue(len(match) == 1)