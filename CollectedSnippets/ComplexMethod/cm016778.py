def encode_token_weights(self, token_weight_pairs):
        token_weight_pairs_l = token_weight_pairs["l"]
        token_weight_pairs_g = token_weight_pairs["g"]
        token_weight_pairs_t5 = token_weight_pairs["t5xxl"]
        token_weight_pairs_llama = token_weight_pairs["llama"]
        lg_out = None
        pooled = None
        extra = {}

        if len(token_weight_pairs_g) > 0 or len(token_weight_pairs_l) > 0:
            if self.clip_l is not None:
                lg_out, l_pooled = self.clip_l.encode_token_weights(token_weight_pairs_l)
            else:
                l_pooled = torch.zeros((1, 768), device=comfy.model_management.intermediate_device())

            if self.clip_g is not None:
                g_out, g_pooled = self.clip_g.encode_token_weights(token_weight_pairs_g)
            else:
                g_pooled = torch.zeros((1, 1280), device=comfy.model_management.intermediate_device())

            pooled = torch.cat((l_pooled, g_pooled), dim=-1)

        if self.t5xxl is not None:
            t5_output = self.t5xxl.encode_token_weights(token_weight_pairs_t5)
            t5_out, t5_pooled = t5_output[:2]
        else:
            t5_out = None

        if self.llama is not None:
            ll_output = self.llama.encode_token_weights(token_weight_pairs_llama)
            ll_out, ll_pooled = ll_output[:2]
            ll_out = ll_out[:, 1:]
        else:
            ll_out = None

        if t5_out is None:
            t5_out = torch.zeros((1, 128, 4096), device=comfy.model_management.intermediate_device())

        if ll_out is None:
            ll_out = torch.zeros((1, 32, 1, 4096), device=comfy.model_management.intermediate_device())

        if pooled is None:
            pooled = torch.zeros((1, 768 + 1280), device=comfy.model_management.intermediate_device())

        extra["conditioning_llama3"] = ll_out
        return t5_out, pooled, extra