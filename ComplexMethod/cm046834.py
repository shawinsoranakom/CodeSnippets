def test_embedding_lr_param_group_split(self):
        """Embedding params can be split into a separate group with custom LR."""
        # This tests the logic that make_q_galore_param_groups produces groups
        # that can be further split by the trainer for embedding LR.
        model = nn.Module()
        model.q_proj = nn.Linear(64, 64, bias = False)
        model.embed = nn.Embedding(100, 64)

        groups = make_q_galore_param_groups(model, rank = 8, weight_quant = False)

        # Simulate splitting non-GaLore group for embedding LR
        embed_lr = 5e-5
        new_groups = []
        for group in groups:
            if "rank" in group:
                new_groups.append(group)
                continue
            embed_params = []
            other_params = []
            for p in group["params"]:
                # In real usage, we'd check the name; here just split by shape
                if p.shape[0] == 100:  # embedding
                    embed_params.append(p)
                else:
                    other_params.append(p)
            if other_params:
                g = dict(group)
                g["params"] = other_params
                new_groups.append(g)
            if embed_params:
                g = dict(group)
                g["params"] = embed_params
                g["lr"] = embed_lr
                new_groups.append(g)

        # Should have 3 groups: galore, non-galore non-embed, embed
        embed_groups = [g for g in new_groups if g.get("lr") == embed_lr]
        assert len(embed_groups) == 1
        assert embed_groups[0]["lr"] == embed_lr