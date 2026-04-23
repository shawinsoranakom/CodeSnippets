def get_data(dataset_name):
    print("Getting dataset: %s" % dataset_name)

    if dataset_name == "lfw_people":
        X = fetch_lfw_people().data
    elif dataset_name == "20newsgroups":
        X = fetch_20newsgroups_vectorized().data[:, :100000]
    elif dataset_name == "olivetti_faces":
        X = fetch_olivetti_faces().data
    elif dataset_name == "rcv1":
        X = fetch_rcv1().data
    elif dataset_name == "CIFAR":
        if handle_missing_dataset(CIFAR_FOLDER) == 0:
            return
        X1 = [unpickle("%sdata_batch_%d" % (CIFAR_FOLDER, i + 1)) for i in range(5)]
        X = np.vstack(X1)
        del X1
    elif dataset_name == "SVHN":
        if handle_missing_dataset(SVHN_FOLDER) == 0:
            return
        X1 = sp.io.loadmat("%strain_32x32.mat" % SVHN_FOLDER)["X"]
        X2 = [X1[:, :, :, i].reshape(32 * 32 * 3) for i in range(X1.shape[3])]
        X = np.vstack(X2)
        del X1
        del X2
    elif dataset_name == "low rank matrix":
        X = make_low_rank_matrix(
            n_samples=500,
            n_features=int(1e4),
            effective_rank=100,
            tail_strength=0.5,
            random_state=random_state,
        )
    elif dataset_name == "uncorrelated matrix":
        X, _ = make_sparse_uncorrelated(
            n_samples=500, n_features=10000, random_state=random_state
        )
    elif dataset_name == "big sparse matrix":
        sparsity = int(1e6)
        size = int(1e6)
        small_size = int(1e4)
        data = np.random.normal(0, 1, int(sparsity / 10))
        data = np.repeat(data, 10)
        row = np.random.uniform(0, small_size, sparsity)
        col = np.random.uniform(0, small_size, sparsity)
        X = sp.sparse.csr_array((data, (row, col)), shape=(size, small_size))
        del data
        del row
        del col
    else:
        X = fetch_openml(dataset_name).data
    return X