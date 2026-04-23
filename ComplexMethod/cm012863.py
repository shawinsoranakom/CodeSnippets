def _calculate_qparams(self, signed: bool, min_val=None, max_val=None):
        if min_val is not None:
            self.min_val = min_val
        if max_val is not None:
            self.max_val = max_val

        # compute alpha
        alpha = torch.max(-self.min_val, self.max_val)

        # check for valid inputs of b, k
        if not self.k or self.k == 0:
            raise AssertionError(f"k must be a non-zero integer, got k={self.k}")
        if self.b % self.k != 0:
            raise AssertionError(
                f"b must be divisible by k, got b={self.b}, k={self.k}"
            )

        # compute n and store as member variable
        self.n = self.b // self.k

        # store a tensor of subtensors (all levels)
        p_all = []

        # create levels
        for i in range(self.n):
            p_curr = torch.tensor([0])

            for j in range((2**self.k - 2) + 1):
                curr_ele = 2 ** (-(i + j * self.n))
                p_append = torch.tensor([curr_ele])
                p_curr = torch.cat((p_curr, p_append))
                # introduce signed numbers
                if signed:
                    p_curr = torch.cat((p_curr, torch.tensor([-curr_ele])))

            if signed:
                # sort tensor in reverse order before adding to list if signed
                sorted, _indices = torch.sort(p_curr, descending=True)
                p_all.append(sorted)
            else:
                p_all.append(p_curr)

        # gamma calculation:
        # loop through all tensors
        # if signed, add element at index 0 for each tensor
        # else, add element at index 1 for each tensor
        # gamma defined to ensure alpha is at max of range
        p_sum = 0.0
        for tens in p_all:
            if signed:
                p_sum += float(tens[0])
            else:
                p_sum += float(tens[1])

        # assign gamma
        gamma = alpha / p_sum

        # calculate cartesian product
        cartesian_product = list(itertools.product(*p_all))

        quantization_levels_list = []

        # calculate sum of each row
        for row in cartesian_product:
            sum = 0.0
            for ele in row:
                sum += ele
            quantization_levels_list.append(sum)

        quantization_levels_gamma = [
            float(gamma) * ele for ele in quantization_levels_list
        ]
        quantization_levels = torch.tensor(quantization_levels_gamma)
        level_indices = torch.tensor([])
        quantization_levels, level_indices = quantization_levels.sort()

        return (alpha, gamma, quantization_levels, level_indices)