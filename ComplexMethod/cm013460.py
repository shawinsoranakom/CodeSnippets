def create_arg(self, a: object) -> fx.node.Node:
        if isinstance(a, torch.nn.Parameter):
            for n, p in self.root.named_parameters():
                if a is p:
                    return self.create_node("get_attr", n, (), {})

            qualname = self.get_fresh_qualname("_param_constant")
            setattr(self.root, qualname, a)

            return self.create_node("get_attr", qualname, (), {})
        elif isinstance(a, py_sym_types):
            if a.node.constant is None:
                raise AssertionError("a.node.constant should not be None")
            return a.node.constant

        # Try reconstructing untracked opaque reference types from existing
        # graph inputs (e.g. derive a DeviceMesh submesh from its root mesh).
        if isinstance(a, (FakeScriptObject, OpaqueBase)):
            node = self._try_reconstruct_opaque(a)
            if node is not None:
                return node

        return super().create_arg(a)