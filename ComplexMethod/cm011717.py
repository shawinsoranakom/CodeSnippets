def compute_dependencies(self) -> None:
        """
        Create dependency edges between nodes, handling aliasing and
        mutation properly.
        """

        class DedupList(Generic[_T]):
            """
            This data structure behaves like a list except it makes sure the
            elements remain unique.
            Normally one could use a OrderedSet/dict for this purpose however
            the list in question gets elements appended as it is being
            iterated over which means that we need to keep the list
            semantics.
            """

            def __init__(
                self,
                items: list[_T] | None = None,
                membership: OrderedSet[_T] | None = None,
            ) -> None:
                self.items = items or []
                self.membership = membership or OrderedSet()

            def append(self, node_user: _T) -> None:
                if node_user in self.membership:
                    return
                self.items.append(node_user)
                self.membership.add(node_user)

            def __add__(self, other: DedupList[_T]) -> DedupList[_T]:
                new_membership = OrderedSet.union(self.membership, other.membership)
                new_items = self.items + [
                    x for x in other.items if x not in self.membership
                ]
                return DedupList(new_items, new_membership)

        # pyrefly: ignore [not-a-type]
        name_to_users: defaultdict[str, DedupList[NodeUser]] = collections.defaultdict(
            DedupList
        )

        # handle aliasing by using python aliasing in name_to_users
        # if foo aliases bar then we will make name_to_users["foo"] point
        # to the same python list as name_to_users["bar"]
        for node in self.nodes:
            for buf1 in node.get_outputs():
                buf1_name = buf1.get_name()
                # This is for handling auto functionized ops which return None
                # and mutate more than 1 inputs, we shouldn't let them all
                # point to the same user list since buffers in the aliases
                # list might not be alias to each other.
                if (
                    isinstance(buf1.node.layout, ir.NoneLayout)
                    and len(buf1.get_aliases()) > 1
                ):
                    continue
                for buf2_name in buf1.get_aliases():
                    if buf1_name in name_to_users and buf2_name in name_to_users:
                        # merge the two
                        list1 = name_to_users[buf1_name]
                        list2 = name_to_users[buf2_name]
                        combined = list1 + list2
                        for key in name_to_users:
                            if (
                                name_to_users[key] is list1
                                or name_to_users[key] is list2
                            ):
                                name_to_users[key] = combined
                    elif buf1_name in name_to_users:
                        name_to_users[buf2_name] = name_to_users[buf1_name]
                    else:
                        name_to_users[buf1_name] = name_to_users[buf2_name]

        # pyrefly: ignore [not-a-type]
        def rename(n: str) -> str:
            if n in self.mutation_renames:
                return rename(self.mutation_renames[n])
            return n

        def add_user(
            # pyrefly: ignore [not-a-type]
            used_by_name: str,
            user_node: BaseSchedulerNode | OutputNode,
            can_inplace: bool = False,
            is_weak: bool = False,
        ) -> None:
            name_to_users[rename(used_by_name)].append(
                NodeUser(user_node, can_inplace, is_weak)
            )

        # pyrefly: ignore [not-a-type, unsupported-operation]
        unbacked_symbol_to_origin_node: dict[sympy.Symbol, str | None] = {}

        # NB: None means that the dependency is on an input.  Don't actually
        # generate a dependency because if we do, Inductor will start trying
        # to free the unbacked int but that's pointless
        for val in V.graph.graph_inputs.values():
            if isinstance(val, sympy.Expr):
                for fs in val.free_symbols:
                    unbacked_symbol_to_origin_node[fs] = None
            elif isinstance(val, ir.TensorBox):
                # We also need to add symbols from input size as well because
                # AOTI doesn't lift the unbacked symints to inputs
                sym_size = [s for s in val.get_size() if isinstance(s, sympy.Expr)]
                for s in sym_size:
                    for fs in s.free_symbols:
                        unbacked_symbol_to_origin_node[fs] = None

        has_non_input_unbacked_defs = False
        for node in self.nodes:
            assert node.node is not None
            # unbacked symbols don't follow ordinary buffer dependencies, so
            # we track their def/uses separately
            unbacked_symbol_defs = sorted(
                node.node.get_unbacked_symbol_defs(), key=lambda x: x.name
            )
            for s in unbacked_symbol_defs:
                assert isinstance(s, sympy.Symbol)
                # Pick the first definer as canonical.  There may be multiple
                # because if a MultiOutputLayout buffer propagates an unbacked
                # symint to multiple outputs, they will all claim to def it.
                has_non_input_unbacked_defs = True
                if s not in unbacked_symbol_to_origin_node:
                    unbacked_symbol_to_origin_node[s] = node.get_name()

        for node in self.nodes:
            log.debug("scheduling %s", node.node)

            if has_non_input_unbacked_defs:
                assert node.node is not None

                unbacked_symbol_uses = sorted(
                    node.node.get_free_symbol_uses(unbacked_only=True),
                    key=lambda x: x.name,
                )
                # if a kernel takes unbacked symints, register dependencies
                for s in unbacked_symbol_uses:
                    assert s in unbacked_symbol_to_origin_node, (
                        f"{s} not in {unbacked_symbol_to_origin_node}"
                    )
                    if (r := unbacked_symbol_to_origin_node[s]) is not None:
                        for buf in self.name_to_node[r].get_outputs():
                            node.add_fake_dep(StarDep(buf.get_name()))

            if (
                len(node.read_writes.writes) == 1
                and (dep := next(iter(node.read_writes.writes)))
                and isinstance(dep, MemoryDep)
            ):
                node_mode = dep.mode
            else:
                node_mode = None

            # Handle output mutations
            for buf in node.get_outputs():
                # a node will mutate either 0 or 1 buffers
                assert len(buf.get_mutations()) <= 1
                for alt_name in buf.get_mutations():
                    alt_name = rename(alt_name)
                    # this node must run after the prior writer
                    add_user(alt_name, node)
                    node.add_fake_dep(StarDep(alt_name, mode=node_mode))
                    for user in name_to_users[alt_name].items:
                        if user.get_name() == node.get_name():
                            continue

                        assert isinstance(user.node, BaseSchedulerNode)
                        for out_buf in user.node.get_outputs():
                            other_name = out_buf.get_name()
                            # this node must run after all prior readers
                            other_name = rename(other_name)
                            # Check if the prior reader is a true alias (view) vs a clone.
                            # Views share underlying storage with the mutated buffer, so we
                            # need a real dependency (is_fake=False) to keep the view's
                            # buffer alive until after this mutation completes. Clones have
                            # independent storage, so we only need an ordering dependency
                            # (is_fake=True) that won't extend their buffer lifetime.
                            is_alias = alt_name in out_buf.get_aliases()
                            node.add_fake_dep(
                                WeakDep(
                                    other_name,
                                    mutating_buf=buf.get_name(),
                                    is_fake=not is_alias,
                                )
                            )
                            add_user(other_name, node, is_weak=True)

            for add_dep in V.graph.additional_buffer_deps[node.get_name()]:
                add_user(add_dep, node, is_weak=True)
                # is_fake=True because these are control dependencies for ordering only,
                # they should not extend buffer lifetimes
                node.add_fake_dep(WeakDep(add_dep, node.get_name(), is_fake=True))

            for add_dep in V.graph.additional_star_deps[node.get_name()]:
                add_user(add_dep, node, is_weak=False)  # Strong dependency
                node.add_fake_dep(StarDep(add_dep))

            # add normal non-mutation dependencies
            for read in node.read_writes.reads:
                if not isinstance(read, WeakDep):
                    add_user(read.name, node, node.can_inplace(read))

            node.update_mutated_names(self.mutation_renames)

            # update our renaming scheme for the next iteration
            for buf in node.get_outputs():
                for alt_name in buf.get_mutations():
                    self.mutation_renames[rename(alt_name)] = buf.get_name()
                    self.mutation_renames[alt_name] = buf.get_name()
                    self.mutation_real_name[buf.get_name()] = (
                        self.mutation_real_name.get(alt_name, alt_name)
                    )

        # make sure outputs aren't dead-code-eliminated
        for buf_name in V.graph.get_output_names():
            log.debug("scheduling output %s", buf_name)
            add_user(buf_name, OutputNode(StarDep(buf_name)))

        # make sure unbacked symints aren't dead-code-eliminated
        if has_non_input_unbacked_defs:
            for out in V.graph.graph_outputs:
                for s in out.get_free_symbol_uses(unbacked_only=True):
                    assert s in unbacked_symbol_to_origin_node, (
                        f"{s} not in {unbacked_symbol_to_origin_node.keys()}"
                    )
                    if r := unbacked_symbol_to_origin_node[s]:
                        for buf_name in self.name_to_node[r].get_buffer_names():
                            log.debug(
                                "scheduling output %s for unbacked symint %s",
                                buf_name,
                                s,
                            )
                            add_user(buf_name, OutputNode(StarDep(buf_name)))

        # make sure input mutation isn't dead-code-eliminated
        for name in self.mutation_renames:
            if name in V.graph.graph_inputs:
                add_user(name, OutputNode(StarDep(name)))
                V.graph.mutated_inputs.add(name)
            elif name in V.graph.constants:
                # In AOTI, module parameters and buffers are not lifted as graph inputs
                add_user(name, OutputNode(StarDep(name)))

        inp_names = {
            name: index for index, name in enumerate(V.graph.graph_inputs.keys())
        }
        V.graph.mutated_input_idxs = [
            inp_names[name] for name in V.graph.mutated_inputs
        ]

        # copy users information onto the nodes
        for node in self.nodes:
            for buf in node.get_outputs():
                buf.set_users(name_to_users[buf.get_name()].items)

        for name in self.name_to_donated_buffer:
            self.name_to_donated_buffer[name].set_users(name_to_users[name].items)

        # For debug logging
        logbuf = IndentedBuffer()
        logbuf.splice("{")
        for key, value in name_to_users.items():
            with logbuf.indent():
                users = [v.get_name() for v in value.items]
                logbuf.splice(f"'{key}': {users},")
        logbuf.splice("}")
        str = logbuf.getrawvalue().rstrip()
        compute_dependencies_log.debug("BUFFER USER LIST\n")
        compute_dependencies_log.debug("===== AFTER SCHEDULING =====\n%s", str)