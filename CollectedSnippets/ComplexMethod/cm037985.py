def _handle_expert_scale_broadcasting(
        self, weights: list[tuple[str, torch.Tensor]], params_dict: dict
    ) -> tuple[list[tuple[str, torch.Tensor]], set[str]]:
        """Handle expert scale parameters that need broadcasting.

        ModelOpt checkpoints use a single value tensor scalar for BMM style
        experts, vLLM expects the scale to be broadcasted across all experts.
        """
        regular_weights = []
        expert_scale_weights = []
        updated_params = set()

        for name, weight in weights:
            # Check if this is an expert scale parameter that needs broadcasting
            if (
                "feed_forward.experts." in name
                and "scale" in name
                and ".shared_expert" not in name
            ):
                if name in params_dict:
                    param = params_dict[name]
                    if (
                        hasattr(param, "data")
                        and param.data.numel() > 1
                        and weight.numel() == 1
                    ):
                        # Broadcast single value to all experts
                        param.data.fill_(weight.item())
                        updated_params.add(name)
                        continue

                expert_scale_weights.append((name, weight))
            else:
                regular_weights.append((name, weight))

        return regular_weights, expert_scale_weights, updated_params