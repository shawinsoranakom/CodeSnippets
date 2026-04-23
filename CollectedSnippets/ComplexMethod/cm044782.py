def batched_params(self, param_group, group_params_names):
        """
        This function returns (technically, yields) a list of
          of tuples (p, state), where
        p is a `fake` parameter that is stacked (over axis 0) from real parameters
        that share the same shape, and its gradient is also stacked;
        `state` is the state corresponding to this batch of parameters
        (it will be physically located in the "state" for one of the real
        parameters, the last one that has any particular shape and dtype).

        This function is decorated as a context manager so that it can
        write parameters back to their "real" locations.

        The idea is, instead of doing:
        <code>
          for p in group["params"]:
             state = self.state[p]
             ...
        </code>
        you can do:
        <code>
          with self.batched_params(group["params"]) as batches:
             for p, state, p_names in batches:
                 ...
        </code>

        Args:
          group: a parameter group, which is a list of parameters; should be
                one of self.param_groups.
          group_params_names: name for each parameter in group,
                which is List[str].
        """
        batches = defaultdict(list)  # `batches` maps from tuple (dtype_as_str,*shape) to list of nn.Parameter
        batches_names = defaultdict(list)  # `batches` maps from tuple (dtype_as_str,*shape) to list of str

        assert len(param_group) == len(group_params_names)
        for p, named_p in zip(param_group, group_params_names):
            key = (str(p.dtype), *p.shape)
            batches[key].append(p)
            batches_names[key].append(named_p)

        batches_names_keys = list(batches_names.keys())
        sorted_idx = sorted(range(len(batches_names)), key=lambda i: batches_names_keys[i])
        batches_names = [batches_names[batches_names_keys[idx]] for idx in sorted_idx]
        batches = [batches[batches_names_keys[idx]] for idx in sorted_idx]

        stacked_params_dict = dict()

        # turn batches into a list, in deterministic order.
        # tuples will contain tuples of (stacked_param, state, stacked_params_names),
        # one for each batch in `batches`.
        tuples = []

        for batch, batch_names in zip(batches, batches_names):
            p = batch[0]
            # we arbitrarily store the state in the
            # state corresponding to the 1st parameter in the
            # group.  class Optimizer will take care of saving/loading state.
            state = self.state[p]
            p_stacked = torch.stack(batch)
            grad = torch.stack([torch.zeros_like(p) if p.grad is None else p.grad for p in batch])
            p_stacked.grad = grad
            stacked_params_dict[key] = p_stacked
            tuples.append((p_stacked, state, batch_names))

        yield tuples  # <-- calling code will do the actual optimization here!

        for (stacked_params, _state, _names), batch in zip(tuples, batches):
            for i, p in enumerate(batch):  # batch is list of Parameter
                p.copy_(stacked_params[i])