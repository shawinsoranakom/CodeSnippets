def __call__(self, x):
        x = self.conv(x)
        fpn_list = []
        F = []
        for i in range(len(self.depth)):
            fpn_list.append(np.sum(self.depth[: i + 1]))

        for i, block in enumerate(self.block_list):
            x = block(x)
            for number in fpn_list:
                if i + 1 == number:
                    F.append(x)
        base = F[-1]

        j = 0
        for i, block in enumerate(self.base_block):
            if i % 3 == 0 and i < 6:
                j = j + 1
                b, c, w, h = F[-j - 1].shape
                if [w, h] == list(base.shape[2:]):
                    base = base
                else:
                    base = self.conv_trans[j - 1](base)
                    base = self.bn_block[j - 1](base)
                base = paddle.concat([base, F[-j - 1]], axis=1)
            base = block(base)
        return base