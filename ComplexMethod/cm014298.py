def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        kwargs = {} if kwargs is None else kwargs
        is_compiling = _is_compiling(func, args, kwargs)

        if is_compiling:
            fx_traceback.current_meta["ac_graph_id"] = self.ac_graph_id
            fx_traceback.current_meta["recompute"] = CheckpointPolicy.PREFER_RECOMPUTE

        if func in SAC_IGNORED_OPS:
            return func(*args, **kwargs)

        proxy_mode = None
        graph_len_before = 0
        if is_compiling:
            from torch.fx.experimental.proxy_tensor import get_proxy_mode
            proxy_mode = get_proxy_mode()
            if proxy_mode is not None:
                graph_len_before = len(proxy_mode.tracer.graph.nodes)

        out = func(*args, **kwargs)

        idx = self.func_counter[func]
        self.func_counter[func] += 1

        policy = self.policy_fn(SelectiveCheckpointContext(is_recompute=False, op_output=out),
                                func, *args, **kwargs)
        if isinstance(policy, bool):
            policy = _policy_from_bool(policy)

        if is_compiling:
            if proxy_mode is not None:
                graph = proxy_mode.tracer.graph
                num_new = len(graph.nodes) - graph_len_before
                for node in itertools.islice(reversed(graph.nodes), num_new):
                    node.meta["recompute"] = policy

        if policy in (CheckpointPolicy.MUST_SAVE, CheckpointPolicy.PREFER_SAVE) or is_compiling:
            self.storage[func][idx] = tree_map(lambda x: _VersionWrapper(_detach_helper(x)), out)
        else:
            self.storage[func][idx] = _RECOMPUTE
        return out