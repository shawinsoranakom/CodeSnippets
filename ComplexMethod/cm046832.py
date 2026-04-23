def test_param_group_separation(self):
        """GaLore vs non-GaLore params are correctly separated."""

        # Create a mini-transformer-like model
        model = nn.Module()
        model.q_proj = nn.Linear(64, 64, bias = False)
        model.k_proj = nn.Linear(64, 64, bias = False)
        model.embed = nn.Embedding(100, 64)
        model.norm = nn.LayerNorm(64)

        groups = make_q_galore_param_groups(model, rank = 8, weight_quant = False)

        # Should have 2 groups: galore and non-galore
        assert len(groups) == 2

        galore_group = [g for g in groups if "rank" in g][0]
        non_galore_group = [g for g in groups if "rank" not in g][0]

        # q_proj and k_proj should be in galore group (2 params)
        assert len(galore_group["params"]) == 2
        # embed and norm should be in non-galore group
        assert (
            len(non_galore_group["params"]) == 3
        )