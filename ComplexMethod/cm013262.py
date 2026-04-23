def _verify_osd(
        self,
        model: nn.Module,
        optim: torch.optim.Optimizer,
        osd: dict[str, Any],
        dist_osd: dict[str, Any],
    ) -> None:
        params = list(chain.from_iterable(g["params"] for g in optim.param_groups))
        param_pid_mapping = dict(zip(params, range(len(params)), strict=True))
        fqn_pid_mapping = {}
        for fqn, param in model.named_parameters():
            pid = param_pid_mapping[param]
            fqn_pid_mapping[fqn] = pid
            fqn_pid_mapping[pid] = fqn
        # Check optimizer_state_dict state

        self.assertEqual(len(osd[_STATE]), len(dist_osd[_STATE]))
        for pid, states in osd[_STATE].items():
            fqn = fqn_pid_mapping[pid]
            dist_states = dist_osd[_STATE].get(fqn, None)
            self.assertIsNotNone(dist_states, fqn)
            self.assertEqual(len(states), len(dist_states))
            for key, state in states.items():
                dist_state = states.get(key, None)
                self.assertIsNotNone(dist_state)
                self._compare_tensor(state, dist_state)

        # Check optimizer_state_dict param_group
        old_dist_osd_pg = dist_osd[_PG]
        if len(osd[_PG]) != len(dist_osd[_PG]):
            self.assertTrue(len(dist_osd[_PG]) > len(osd[_PG]))
            new_pg = copy.deepcopy(dist_osd[_PG][0])
            new_pg["params"] = []
            for dist_group in dist_osd[_PG]:
                new_pg["params"].extend(dist_group["params"])
            dist_osd[_PG] = [new_pg]

        self.assertEqual(len(osd[_PG]), len(dist_osd[_PG]))
        for group, dist_group in zip(osd[_PG], dist_osd[_PG], strict=True):
            self.assertEqual(len(group), len(dist_group))
            for key, value in group.items():
                # Below doesn't work because param_groups can have None
                # values.
                # dist_value = dist_group.get(key, None)
                # self.assertIsNotNone(dist_value, (dist_group, group))
                dist_value = dist_group[key]
                if key == "params":
                    fqns = [fqn_pid_mapping[pid] for pid in value]
                    self.assertEqual(sorted(fqns), sorted(dist_value))
                else:
                    self.assertEqual(value, dist_value)
        dist_osd[_PG] = old_dist_osd_pg