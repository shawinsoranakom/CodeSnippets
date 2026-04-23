def forward(self, x, attention_mask=None, intermediate_output=None, final_layer_norm_intermediate=True, dtype=None, embeds_info=[]):
        mask = None
        if attention_mask is not None:
            mask = 1.0 - attention_mask.to(x.dtype).reshape((attention_mask.shape[0], 1, -1, attention_mask.shape[-1])).expand(attention_mask.shape[0], 1, attention_mask.shape[-1], attention_mask.shape[-1])
            mask = mask.masked_fill(mask.to(torch.bool), -torch.finfo(x.dtype).max)

        intermediate = None
        optimized_attention = optimized_attention_for_device(x.device, mask=attention_mask is not None, small_input=True)
        past_bias = None

        if intermediate_output is not None:
            if intermediate_output < 0:
                intermediate_output = len(self.block) + intermediate_output

        for i, l in enumerate(self.block):
            x, past_bias = l(x, mask, past_bias, optimized_attention)
            if i == intermediate_output:
                intermediate = x.clone()
        x = self.final_layer_norm(x)
        if intermediate is not None and final_layer_norm_intermediate:
            intermediate = self.final_layer_norm(intermediate)
        return x, intermediate