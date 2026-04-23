def find_movable_constructors(
        self, graph: fx.Graph, constructors: list[fx.Node]
    ) -> OrderedSet[fx.Node]:
        """
        Starting from the cpu constructors, iterate through the graph and test that all of their
        downstream uses can safely be moved to cpu.
        """
        cpu_indeg: dict[fx.Node, int] = self.get_cpu_indeg_count(graph)

        # which constructors cannot be moved to gpu
        cannot_move_to_gpu = OrderedSet[fx.Node]()

        # For any node in the graph, which constructors does it have a dependency on
        constructor_dependencies: dict[fx.Node, OrderedSet[fx.Node]] = defaultdict(
            OrderedSet
        )

        # if a cpu node has a dependency on two different cpu constructors,
        # then if either constructor cannot be moved to gpu, the other cannot as well.
        # In this case any node with a dependency on one will have a dependency on the other
        equal_constructor_sets: dict[fx.Node, OrderedSet[fx.Node]] = {
            c: OrderedSet([c]) for c in constructors
        }

        def make_dependencies_equivalent(
            set1: OrderedSet[fx.Node], set2: OrderedSet[fx.Node]
        ) -> OrderedSet[fx.Node]:
            # could use union find but not worth complexity here
            set1.update(set2)
            for obj in set1:
                equal_constructor_sets[obj] = set1
            return set1

        queue: list[fx.Node] = list(constructors)

        for c in queue:
            constructor_dependencies[c].add(c)

        while queue:
            node = queue.pop()
            dependencies = constructor_dependencies[node]

            for user in node.users:
                if self.cannot_be_moved(user):
                    cannot_move_to_gpu.update(dependencies)
                    break

                # this node was used on a op which takes in multiple devices and output a gpu
                # tensor. we can convert its cpu input to gpu without making further changes
                if self.allow_cpu_device(user) and self.is_on_target_device(user):
                    del cpu_indeg[user]
                elif (
                    self.allow_inputs
                    and self.is_on_target_device(user)
                    and self.all_inputs_are_cpu_scalar_or_on_target_device(user)
                ):
                    # this node takes only cpu scalar tensors or gpu tensors as inputs
                    # and outputs a gpu tensor. we can convert its cpu scalar inputs to gpu
                    # without making further changes
                    del cpu_indeg[user]
                else:
                    # otherwise, we should continue look at its downstream uses
                    cpu_indeg[user] -= 1
                    if cpu_indeg[user] == 0:
                        del cpu_indeg[user]
                        queue.append(user)

                unioned_set = make_dependencies_equivalent(
                    dependencies, constructor_dependencies[user]
                )
                constructor_dependencies[user] = unioned_set

        for node in cpu_indeg:
            if constructor_dependencies[node]:
                cannot_move_to_gpu.update(constructor_dependencies[node])

        all_cannot_move_to_gpu = cannot_move_to_gpu.copy()
        for constructor in cannot_move_to_gpu:
            all_cannot_move_to_gpu.update(equal_constructor_sets[constructor])

        return OrderedSet(constructors) - all_cannot_move_to_gpu