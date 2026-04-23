def _fuse_gate_up_proj(self, weights: Iterable[WeightItem]) -> Iterable[WeightItem]:
        """Fuse gate_proj and up_proj into gate_up_proj."""
        mlp_buf: dict[int, dict[str, torch.Tensor]] = defaultdict(dict)
        mlp_suffixes = {
            "mlp.gate_proj.weight": "gate",
            "mlp.up_proj.weight": "up",
        }

        for name, tensor in weights:
            m = _LAYER_RE.match(name)
            if m and m.group(2) in mlp_suffixes:
                layer_idx = int(m.group(1))
                mlp_buf[layer_idx][mlp_suffixes[m.group(2)]] = tensor
            else:
                yield name, tensor

        # Yield fused gate_up weights
        for layer_idx in sorted(mlp_buf.keys()):
            parts = mlp_buf[layer_idx]
            if all(p in parts for p in ("gate", "up")):
                fused = torch.cat([parts["gate"], parts["up"]], dim=0)
                yield f"layers.{layer_idx}.mlp.gate_up_proj.weight", fused
            elif parts:
                missing = [p for p in ("gate", "up") if p not in parts]
                raise ValueError(f"Layer {layer_idx} missing MLP parts: {missing}")