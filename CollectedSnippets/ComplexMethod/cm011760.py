def single_index_in_fused_node(buf_to_be_inplaced: SchedulerBuffer) -> bool:
            # Inside of NodeUser, we track that the read and write are equivalent
            # before deciding if the use can be inplace.
            # But if that use is fused into a larger kernel, we need to check equivalence
            # of other accesses in fused scheduler node as well.
            fused_node = buf_to_be_inplaced.scheduler.get_fused_node(self)
            buf_name = buf_to_be_inplaced.get_name()
            # Dedup read/writes with equivalent indices
            # TODO - would be nice if we could just cache accesses on ReadWrites,
            # and enforce variant that this class & members are functional..
            deps: OrderedSet[Dep] = OrderedSet()
            for user in buf_to_be_inplaced.users:
                user_node = user.node
                if not isinstance(user_node, BaseSchedulerNode):
                    continue

                if (
                    user_node.get_first_name()
                    not in buf_to_be_inplaced.scheduler.name_to_fused_node
                    or buf_to_be_inplaced.scheduler.get_fused_node(user_node)
                    is not fused_node
                ):
                    continue

                deps |= (
                    o
                    for o in user_node.read_writes.reads_and_writes()
                    if o.name == buf_name
                )
                if len(deps) > 1:
                    return False

            return True