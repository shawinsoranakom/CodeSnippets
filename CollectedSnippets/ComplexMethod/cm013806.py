def _any_version_depends_on_gradient(self) -> set[int]:
        """Extract IDs of Tensors which depend or will depend on a gradient.

        Note that this weakened definition of "depends" requires us to loop
        over the data flow graph multiple times because it allows dependency
        information to flow backward through edges and removes the guarantee
        that nodes are topologically sorted. (Or indeed, even that a valid
        topological order exists.) Put another way, we have converted an
        acyclic data flow graph into a cyclic graph and we are attempting to
        partition cycles involving a gradient from the rest of the graph.
        """
        depends_on_gradient: set[int] = set()
        while True:
            start_size = len(depends_on_gradient)
            for node in self._data_flow_graph.flow_nodes:
                ids = tuple(
                    key.id
                    for key, (_, version) in node.inputs.items()
                    if self._categories.get(key, version)
                    in (Category.GRADIENT, Category.PARAMETER)
                    or key.id in depends_on_gradient
                )

                if ids:
                    depends_on_gradient.update(ids)

                    depends_on_gradient.update(key.id for key in node.outputs)

            # We are guaranteed to exit because there is a finite set of
            # TensorAndID pairs. In practice we do not expect to loop more than
            # three times: once to identify the core parameter update loop,
            # once to fold the first step into that loop, and a third time
            # where no new elements are added.
            if len(depends_on_gradient) == start_size:
                return depends_on_gradient