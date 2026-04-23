def generate_data(transform):
    torch.manual_seed(1)
    while isinstance(transform, IndependentTransform):
        transform = transform.base_transform
    if isinstance(transform, ReshapeTransform):
        return torch.randn(transform.in_shape)
    if isinstance(transform.inv, ReshapeTransform):
        return torch.randn(transform.inv.out_shape)
    domain = transform.domain
    while (
        isinstance(domain, constraints.independent)
        and domain is not constraints.real_vector
    ):
        domain = domain.base_constraint
    codomain = transform.codomain
    x = torch.empty(4, 5)
    positive_definite_constraints = [
        constraints.lower_cholesky,
        constraints.positive_definite,
    ]
    if domain in positive_definite_constraints:
        x = torch.randn(6, 6)
        x = x.tril(-1) + x.diag().exp().diag_embed()
        if domain is constraints.positive_definite:
            return x @ x.T
        return x
    elif codomain in positive_definite_constraints:
        return torch.randn(6, 6)
    elif domain is constraints.real:
        return x.normal_()
    elif domain is constraints.real_vector:
        # For corr_cholesky the last dim in the vector
        # must be of size (dim * dim) // 2
        x = torch.empty(3, 6)
        x = x.normal_()
        return x
    elif domain is constraints.positive:
        return x.normal_().exp()
    elif domain is constraints.unit_interval:
        return x.uniform_()
    elif isinstance(domain, constraints.interval):
        x = x.uniform_()
        x = x.mul_(domain.upper_bound - domain.lower_bound).add_(domain.lower_bound)
        return x
    elif domain is constraints.simplex:
        x = x.normal_().exp()
        x /= x.sum(-1, True)
        return x
    elif domain is constraints.corr_cholesky:
        x = torch.empty(4, 5, 5)
        x = x.normal_().tril()
        x /= x.norm(dim=-1, keepdim=True)
        x.diagonal(dim1=-1).copy_(x.diagonal(dim1=-1).abs())
        return x
    raise ValueError(f"Unsupported domain: {domain}")