def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = [x + 0.1 * i for i in range(self.seq_len)]
        x2 = [self.seq1[i](x1[i]) for i in range(self.seq_len)]
        x3 = [x2[i] - 0.1 * i for i in range(self.seq_len)]
        x4 = [x1[i] for i in range(3)] + [x3[i] for i in range(3, self.seq_len)]
        x5 = [self.seq2[i](x4[i]) for i in range(self.seq_len)]
        x6 = [x5[i] + 0.1 * (self.seq_len - i) for i in range(self.seq_len)]
        x7 = (
            [x1[i] for i in range(4)]
            + [x3[i] for i in range(6, 8)]
            + [x6[i] for i in range(4)]
        )
        x8 = [self.seq3[i](x7[i]) for i in range(self.seq_len)]
        x9 = torch.cat(x8, dim=1)
        return x9