def forward(self, x, mask=None, intermediate_output=None):
        optimized_attention = optimized_attention_for_device(x.device, mask=mask is not None, small_input=True)

        all_intermediate = None
        if intermediate_output is not None:
            if intermediate_output == "all":
                all_intermediate = []
                intermediate_output = None
            elif intermediate_output < 0:
                intermediate_output = len(self.layers) + intermediate_output

        intermediate = None
        for i, l in enumerate(self.layers):
            x = l(x, mask, optimized_attention)
            if i == intermediate_output:
                intermediate = x.clone()
            if all_intermediate is not None:
                all_intermediate.append(x.unsqueeze(1).clone())

        if all_intermediate is not None:
            intermediate = torch.cat(all_intermediate, dim=1)

        return x, intermediate