def forward(self, attention_mask: Tensor | None = None, bbox: dict[str, Any] | None = None) -> Tensor:
        # re-using pretrained model with subsequent addition of prefix_bucket
        if self.expand and self.prefix_bucket:
            new_bias = nn.Embedding(self.relative_attention_num_buckets + 2, self.num_heads)
            new_bias.weight.data[: self.relative_attention_num_buckets] = self.relative_attention_bias.weight.data
            new_bias.weight.data[self.relative_attention_num_buckets :] = 0.1
            self.relative_attention_bias = new_bias
            self.expand = False

        rp_bucket = self.get_bucket(attention_mask, bbox)

        if self.prefix_bucket:
            if rp_bucket.size(0) == 1 and attention_mask.size(0) > 1:
                rp_bucket = rp_bucket.repeat(attention_mask.size(0), 1, 1)
            # based on assumption that prefix bboxes are negative
            is_prefix = bbox[:, :, 1] < 0
            num_prefix = is_prefix.sum(-1)
            for idx, num_prefix_row in enumerate(num_prefix.cpu().numpy()):
                rp_bucket[idx, :num_prefix_row, num_prefix_row:] = self.relative_attention_num_buckets
                rp_bucket[idx, num_prefix_row:, :num_prefix_row] = self.relative_attention_num_buckets + 1

        values: Tensor = self.relative_attention_bias(rp_bucket)
        if values.dim() != 4:
            raise ValueError("Wrong dimension of values tensor")
        values = values.permute([0, 3, 1, 2])

        return values