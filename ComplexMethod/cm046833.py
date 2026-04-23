def test_bias_excluded_from_galore(self):
        """1D bias params matching target names must NOT be in the GaLore group.

        GaLoreProjector.project requires 2-D gradients, so bias vectors
        (e.g. q_proj.bias) that match a target name must be excluded.
        """
        model = nn.Module()
        model.q_proj = nn.Linear(64, 64, bias = True)  # has .weight AND .bias
        model.embed = nn.Embedding(100, 64)

        groups = make_q_galore_param_groups(model, rank = 8, weight_quant = False)

        galore_group = [g for g in groups if "rank" in g][0]
        non_galore_group = [g for g in groups if "rank" not in g][0]

        # Only the 2-D q_proj.weight should be in the GaLore group
        assert len(galore_group["params"]) == 1
        assert galore_group["params"][0].dim() == 2

        # q_proj.bias (1-D) + embed.weight should be in non-GaLore
        assert any(p.dim() == 1 for p in non_galore_group["params"])