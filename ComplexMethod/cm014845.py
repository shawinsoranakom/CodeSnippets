def _broadcast(t, batch_broadcasted, num_heads_broadcasted):
            if batch_broadcasted and num_heads_broadcasted:
                # (1, seq_len, 1, head_dim) -> (batch, seq_len, num_heads, head_dim)
                result = torch.nested.nested_tensor(
                    [t[0].expand(-1, num_heads, t.size(-1)) for _ in range(batch)], dtype=torch.float32)
            elif batch_broadcasted:
                # (1, seq_len, num_heads, head_dim) -> (batch, seq_len, num_heads, head_dim)
                result = torch.nested.nested_tensor([t[0] for _ in range(batch)], dtype=torch.float32)
            elif num_heads_broadcasted:
                # (batch, seq_len, 1, head_dim) -> (batch, seq_len, num_heads, head_dim)
                result = torch.nested.nested_tensor([x.expand(-1, num_heads, t.size(-1))
                                                    for x in t.unbind()], dtype=torch.float32)
            else:
                result = t.to(torch.float32)
            return result