def __init__(self,  net: network.Network, weights: network.NetworkWeights):
        super().__init__(net, weights)

        self.w1 = weights.w.get("lokr_w1")
        self.w1a = weights.w.get("lokr_w1_a")
        self.w1b = weights.w.get("lokr_w1_b")
        self.dim = self.w1b.shape[0] if self.w1b is not None else self.dim
        self.w2 = weights.w.get("lokr_w2")
        self.w2a = weights.w.get("lokr_w2_a")
        self.w2b = weights.w.get("lokr_w2_b")
        self.dim = self.w2b.shape[0] if self.w2b is not None else self.dim
        self.t2 = weights.w.get("lokr_t2")

    def calc_updown(self, orig_weight):
        if self.w1 is not None:
            w1 = self.w1.to(orig_weight.device)
        else:
            w1a = self.w1a.to(orig_weight.device)
            w1b = self.w1b.to(orig_weight.device)
            w1 = w1a @ w1b

        if self.w2 is not None:
            w2 = self.w2.to(orig_weight.device)
        elif self.t2 is None:
            w2a = self.w2a.to(orig_weight.device)
            w2b = self.w2b.to(orig_weight.device)
            w2 = w2a @ w2b
        else:
            t2 = self.t2.to(orig_weight.device)
            w2a = self.w2a.to(orig_weight.device)
            w2b = self.w2b.to(orig_weight.device)
            w2 = lyco_helpers.make_weight_cp(t2, w2a, w2b)

        output_shape = [w1.size(0) * w2.size(0), w1.size(1) * w2.size(1)]
        if len(orig_weight.shape) == 4:
            output_shape = orig_weight.shape

        updown = make_kron(output_shape, w1, w2)

        return self.finalize_updown(updown, orig_weight, output_shape)
