def make_prob_dist(shape, is_contiguous):
            if is_contiguous:
                if dtype == torch.half or dtype == torch.bfloat16:
                    return torch.zeros(shape, device=device).uniform_().to(dtype=dtype)
                return torch.zeros(shape, device=device, dtype=dtype).uniform_()
            elif len(shape) == 1:
                if dtype == torch.half or dtype == torch.bfloat16:
                    return torch.zeros((shape + [5]), device=device).uniform_().to(dtype=dtype)[:, 2]
                return torch.zeros((shape + [5]), device=device, dtype=dtype).uniform_()[:, 2]
            else:
                # num dim = 2
                new_shape = [2, shape[1], 7, 1, shape[0], 1, 10]
                if dtype == torch.half or dtype == torch.bfloat16:
                    prob_dist = torch.zeros(new_shape, device=device).uniform_().to(dtype=dtype)
                else:
                    prob_dist = torch.zeros(new_shape, device=device, dtype=dtype).uniform_()
                prob_dist = prob_dist.transpose(1, 4)
                prob_dist = prob_dist[1, :, 5, 0, :, 0, 4]
                if prob_dist.is_contiguous():
                    raise AssertionError("expected prob_dist to be non-contiguous")
                return prob_dist