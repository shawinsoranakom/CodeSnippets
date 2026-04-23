def set_subgraph_body(self, body_name: str):
        assert all(
            hasattr(self, field.name) for field in dataclasses.fields(SubgraphInfo)
        )
        old_state = {
            key.name: getattr(self, key.name)
            for key in dataclasses.fields(SubgraphInfo)
        }

        assert body_name in self.subgraph_bodies, body_name

        subgraph = self.subgraph_bodies[body_name]
        for key, value in subgraph.to_dict().items():
            if value is None and key in subgraph.only_copy_if_non_none_fields:
                continue
            setattr(self, key, value)

        context = (
            contextlib.nullcontext
            if not self.ops_handler
            # pyrefly: ignore [not-callable]
            else lambda: V.set_ops_handler(self.ops_handler(V.get_ops_handler()))
        )
        with context():  # type: ignore[operator]
            yield
        self.subgraph_bodies[body_name] = SubgraphInfo(
            **{
                key.name: getattr(self, key.name)
                for key in dataclasses.fields(SubgraphInfo)
            }
        )
        for key, value in old_state.items():
            setattr(self, key, value)