def augment(X, y, reduction_rate, reduction_mask, mixup_rate, mixup_alpha):
    perm = np.random.permutation(len(X))
    for i, idx in enumerate(tqdm(perm)):
        if np.random.uniform() < reduction_rate:
            y[idx] = spec_utils.reduce_vocal_aggressively(X[idx], y[idx], reduction_mask)

        if np.random.uniform() < 0.5:
            # swap channel
            X[idx] = X[idx, ::-1]
            y[idx] = y[idx, ::-1]
        if np.random.uniform() < 0.02:
            # mono
            X[idx] = X[idx].mean(axis=0, keepdims=True)
            y[idx] = y[idx].mean(axis=0, keepdims=True)
        if np.random.uniform() < 0.02:
            # inst
            X[idx] = y[idx]

        if np.random.uniform() < mixup_rate and i < len(perm) - 1:
            lam = np.random.beta(mixup_alpha, mixup_alpha)
            X[idx] = lam * X[idx] + (1 - lam) * X[perm[i + 1]]
            y[idx] = lam * y[idx] + (1 - lam) * y[perm[i + 1]]

    return X, y