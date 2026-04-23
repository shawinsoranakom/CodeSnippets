def encode_token_weights(self, token_weight_pairs):
        token_weight_pairs_l = token_weight_pairs["l"]
        token_weight_pairs_g = token_weight_pairs["g"]
        token_weight_pairs_t5 = token_weight_pairs["t5xxl"]
        lg_out = None
        pooled = None
        out = None
        extra = {}

        if len(token_weight_pairs_g) > 0 or len(token_weight_pairs_l) > 0:
            if self.clip_l is not None:
                lg_out, l_pooled = self.clip_l.encode_token_weights(token_weight_pairs_l)
            else:
                l_pooled = torch.zeros((1, 768), device=comfy.model_management.intermediate_device())

            if self.clip_g is not None:
                g_out, g_pooled = self.clip_g.encode_token_weights(token_weight_pairs_g)
                if lg_out is not None:
                    cut_to = min(lg_out.shape[1], g_out.shape[1])
                    lg_out = torch.cat([lg_out[:,:cut_to], g_out[:,:cut_to]], dim=-1)
                else:
                    lg_out = torch.nn.functional.pad(g_out, (768, 0))
            else:
                g_out = None
                g_pooled = torch.zeros((1, 1280), device=comfy.model_management.intermediate_device())

            if lg_out is not None:
                lg_out = torch.nn.functional.pad(lg_out, (0, 4096 - lg_out.shape[-1]))
                out = lg_out
            pooled = torch.cat((l_pooled, g_pooled), dim=-1)

        if self.t5xxl is not None:
            t5_output = self.t5xxl.encode_token_weights(token_weight_pairs_t5)
            t5_out, t5_pooled = t5_output[:2]
            if self.t5_attention_mask:
                extra["attention_mask"] = t5_output[2]["attention_mask"]

            if lg_out is not None:
                out = torch.cat([lg_out, t5_out], dim=-2)
            else:
                out = t5_out

        if out is None:
            out = torch.zeros((1, 77, 4096), device=comfy.model_management.intermediate_device())

        if pooled is None:
            pooled = torch.zeros((1, 768 + 1280), device=comfy.model_management.intermediate_device())

        return out, pooled, extra