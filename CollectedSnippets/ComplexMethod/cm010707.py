def baddbmm(self, batch1, batch2, beta=1, alpha=1):
    if not self.is_floating_point() and not self.is_complex():
        beta = int(beta)
        alpha = int(alpha)
    result = torch.bmm(batch1, batch2)
    if not isinstance(alpha, numbers.Number) or alpha != 1:
        result = result * alpha
    if beta == 0:
        return result
    if not isinstance(beta, numbers.Number) or beta != 1:
        self = self * beta
    return self + result