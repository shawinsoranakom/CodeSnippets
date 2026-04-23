def size_args(self):
        X = self.input_nodes[0]
        W = self.input_nodes[1]
        Bias = (
            self.input_nodes[2]
            if len(self.input_nodes) == 3
            else self.input_nodes[4]
            if len(self.input_nodes) == 5
            else None
        )
        Y = self.output_node

        M = X.get_size()[-2]
        K = X.get_size()[-1]
        N = W.get_size()[-1]
        LDA = X.get_stride()[-2 if X.get_stride()[-1] == 1 else -1]
        LDB = W.get_stride()[-2 if W.get_stride()[-1] == 1 else -1]
        LDC = Y.get_stride()[-2 if Y.get_stride()[-1] == 1 else -1]
        LDD = (
            0
            if (Bias is None or len(Bias.get_size()) == 1)
            else Bias.get_stride()[-2 if Bias.get_stride()[-1] == 1 else -1]
        )
        if self.is_batched:
            B = X.get_size()[0]
            return B, M, N, K, LDA, LDB, LDC, LDD
        else:
            return M, N, K, LDA, LDB, LDC, LDD