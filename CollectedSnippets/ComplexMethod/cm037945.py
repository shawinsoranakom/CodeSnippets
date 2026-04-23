def _fuse_qkv_proj(self, weights: Iterable[WeightItem]) -> Iterable[WeightItem]:
        """Fuse q_proj, k_proj, v_proj into qkv_proj."""
        qkv_buf: dict[int, dict[str, torch.Tensor]] = defaultdict(dict)
        qkv_suffixes = {
            "self_attn.q_proj.weight": "q",
            "self_attn.k_proj.weight": "k",
            "self_attn.v_proj.weight": "v",
        }

        for name, tensor in weights:
            m = _LAYER_RE.match(name)
            if m and m.group(2) in qkv_suffixes:
                layer_idx = int(m.group(1))
                qkv_buf[layer_idx][qkv_suffixes[m.group(2)]] = tensor
            else:
                yield name, tensor

        # Yield fused QKV weights
        for layer_idx in sorted(qkv_buf.keys()):
            parts = qkv_buf[layer_idx]
            if all(p in parts for p in ("q", "k", "v")):
                fused = torch.cat([parts["q"], parts["k"], parts["v"]], dim=0)
                yield f"layers.{layer_idx}.self_attn.qkv_proj.weight", fused
            elif parts:
                missing = [p for p in ("q", "k", "v") if p not in parts]
                raise ValueError(f"Layer {layer_idx} missing QKV parts: {missing}")