def remove_tensorify_specialized_graphargs(self) -> None:
        # This is a pretty interesting function. Basically we have this problem
        # where our compiler tends to choke when we have unused inputs. The way
        # we support dynamic float arguments is by doing a joint fx pass and
        # tensorifying away as many symfloats as we can. For the remaining symfloats
        # we have no choice but to specialize... HOWEVER at that point in time
        # we can no longer remove graph inputs. So our sledgehammer solution is to
        # save the state of what inputs we should have specialized in dynamo and
        # restart analysis. This function incorporates this "view from the future"
        # state and specializes inputs that we know we won't be able to tensorify
        # away in the joint pass. In principle we shouldn't choke on unused inputs
        # and so this shouldn't be necessary. In practice CUDA graphs choke on
        # unused inputs so we need this for now.

        # Import here to prevent circular import
        from torch._dynamo.symbolic_convert import TensorifyState

        for node in self.graph.nodes:
            example_value = node.meta.get("example_value")
            if (
                isinstance(example_value, FakeTensor)
                and example_value.item_memo is not None
                and hasattr(example_value.item_memo.node._expr, "name")
                and all(u.target == "item" for u in node.users)
                and TensorifyState.should_specialize(
                    # We use _expr instead of expr b/c we want the symbol not the replacement
                    example_value.item_memo.node._expr.name
                )
            ):
                for u in list(node.users):
                    u.replace_all_uses_with(guard_scalar(example_value.item_memo))
                    self.remove_node(u)
                self.remove_node(node)