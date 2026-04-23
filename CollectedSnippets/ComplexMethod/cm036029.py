def forward(self, x: torch.Tensor, mem: List[torch.Tensor]):
        # Length of the memory
        m_len = len(mem[0]) if mem else 0
        # Create a subsequent mask for tokens
        if self.mask_x is None or self.mask_x.shape[0] < len(x):
            from labml_nn.transformers.utils import subsequent_mask
            self.mask_x = subsequent_mask(len(x)).to(x.device)
        # Create an all ones (full visibility) mask for memory
        if self.mask_mem is None or self.mask_mem.shape[1] < m_len or self.mask_mem.shape[0] < len(x):
            self.mask_mem = self.mask_x.new_ones(len(x), m_len, 1)

        # Concatenate the masks if there is memory
        if m_len:
            mask = torch.cat((self.mask_mem[:len(x), :m_len], self.mask_x[:len(x), :len(x)]), dim=1)
        # Use the subsequent mask otherwise
        else:
            mask = self.mask_x[:len(x), :len(x)]

        # Token embeddings
        x = self.src_embed(x)
        # Run it through the transformer
        res, mem = self.transformer(x, mem, mask)
        # Generate logits of the next token
        res = self.generator(res)
        #
        return res, mem