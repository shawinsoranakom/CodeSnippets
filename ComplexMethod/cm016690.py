def forward(self, x: Tensor, vec: Tensor, pe: Tensor, attn_mask=None, modulation_dims=None, transformer_options={}) -> Tensor:
        if self.modulation:
            mod, _ = self.modulation(vec)
        else:
            mod = vec

        transformer_patches = transformer_options.get("patches", {})
        extra_options = transformer_options.copy()

        qkv, mlp = torch.split(self.linear1(apply_mod(self.pre_norm(x), (1 + mod.scale), mod.shift, modulation_dims)), [3 * self.hidden_size, self.mlp_hidden_dim_first], dim=-1)

        q, k, v = qkv.view(qkv.shape[0], qkv.shape[1], 3, self.num_heads, -1).permute(2, 0, 3, 1, 4)
        del qkv
        q, k = self.norm(q, k, v)

        if "attn1_patch" in transformer_patches:
            patch = transformer_patches["attn1_patch"]
            for p in patch:
                out = p(q, k, v, pe=pe, attn_mask=attn_mask, extra_options=extra_options)
                q, k, v, pe, attn_mask = out.get("q", q), out.get("k", k), out.get("v", v), out.get("pe", pe), out.get("attn_mask", attn_mask)

        # compute attention
        attn = attention(q, k, v, pe=pe, mask=attn_mask, transformer_options=transformer_options)
        del q, k, v

        if "attn1_output_patch" in transformer_patches:
            patch = transformer_patches["attn1_output_patch"]
            for p in patch:
                attn = p(attn, extra_options)

        # compute activation in mlp stream, cat again and run second linear layer
        if self.yak_mlp:
            mlp = self.mlp_act(mlp[..., self.mlp_hidden_dim_first // 2:]) * mlp[..., :self.mlp_hidden_dim_first // 2]
        else:
            mlp = self.mlp_act(mlp)
        output = self.linear2(torch.cat((attn, mlp), 2))
        x += apply_mod(output, mod.gate, None, modulation_dims)
        if x.dtype == torch.float16:
            x = torch.nan_to_num(x, nan=0.0, posinf=65504, neginf=-65504)
        return x