def _recursive_maybe_replace_node_with_obs(
        maybe_node: Argument,
        model: torch.nn.Module,
        named_modules: dict[str, torch.nn.Module],
        graph: Graph,
    ) -> Argument:
        """
        Navigate an arbitrary data structure of lists, tuples, dicts.
        For each container type, recurse on all inputs. Once any Node
        is found, insert an observer if needed and do not recurse further.

        For example, given a structure of

          {'foo1': [[bar1]], 'foo2': {'foo3': [[[bar3]]]}}

        we recurse down to bar1 and bar3, observe them if necessary,
        and if we inserted an observer then replace the original node
        with its observer.

        Returns the data structure with all nodes needing observation being
        replaced by their observers.
        """
        if isinstance(maybe_node, Node):
            # check dtype of this node
            arg_as_output_target_dtype = _get_arg_target_dtype_as_output(
                maybe_node, named_modules, obs_or_fq_map, is_qat
            )
            observer_mod = None
            arg_as_input_target_dtype = torch.float
            if "target_dtype_info" in maybe_node.meta:
                observer_cls = maybe_node.meta["target_dtype_info"].get(
                    "input_act_obs_or_fq_ctr", None
                )
                if observer_cls is not None:
                    observer_mod = observer_cls()
                    arg_as_input_target_dtype = observer_mod.dtype
            # TODO: this does not handle dynamic quantization yet
            need_obs = (
                arg_as_output_target_dtype != arg_as_input_target_dtype
                and arg_as_input_target_dtype != torch.float
            )
            if need_obs:
                if observer_mod is None:
                    raise AssertionError(
                        "observer_mod must not be None when need_obs is True"
                    )
                # insert observer
                observer_node = _insert_obs_or_fq(
                    maybe_node, observer_mod, model, named_modules, graph
                )
                return observer_node
            else:
                return maybe_node
        elif isinstance(maybe_node, (list, tuple)):
            results = [
                _recursive_maybe_replace_node_with_obs(
                    inner_node,
                    model,
                    named_modules,
                    graph,
                )
                for inner_node in maybe_node
            ]
            if isinstance(maybe_node, list):
                return results
            else:
                return tuple(results)
        elif isinstance(maybe_node, dict):
            results_dict = {}
            for k, inner_v in maybe_node.items():
                results_dict[k] = _recursive_maybe_replace_node_with_obs(
                    inner_v, model, named_modules, graph
                )
            return results_dict
        elif maybe_node is None:
            return None
        else:
            raise Exception(  # noqa: TRY002
                "Unhandled type for returned node:", maybe_node
            )