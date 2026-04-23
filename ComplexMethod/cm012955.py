def from_params(cls, wi, wh, bi=None, bh=None, split_gates=False):
        """Uses the weights and biases to create a new LSTM cell.

        Args:
            wi, wh: Weights for the input and hidden layers
            bi, bh: Biases for the input and hidden layers
        """
        if (bi is None) != (bh is None):
            raise AssertionError("bi and bh must both be None or both have values")
        input_size = wi.shape[1]
        hidden_size = wh.shape[1]
        cell = cls(
            input_dim=input_size,
            hidden_dim=hidden_size,
            bias=(bi is not None),
            split_gates=split_gates,
        )

        if not split_gates:
            cell.igates.weight = torch.nn.Parameter(wi)
            if bi is not None:
                cell.igates.bias = torch.nn.Parameter(bi)
            cell.hgates.weight = torch.nn.Parameter(wh)
            if bh is not None:
                cell.hgates.bias = torch.nn.Parameter(bh)
        else:
            # split weight/bias
            for w, b, gates in zip([wi, wh], [bi, bh], [cell.igates, cell.hgates]):
                for w_chunk, gate in zip(w.chunk(4, dim=0), gates.values()):  # type: ignore[operator]
                    gate.weight = torch.nn.Parameter(w_chunk)

                if b is not None:
                    for b_chunk, gate in zip(b.chunk(4, dim=0), gates.values()):  # type: ignore[operator]
                        gate.bias = torch.nn.Parameter(b_chunk)

        return cell