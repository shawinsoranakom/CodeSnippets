def test_correct_number_of_clusters(metric, csr_container):
    # in 'auto' mode

    n_clusters = 3
    X = generate_clustered_data(n_clusters=n_clusters)
    # Parameters chosen specifically for this task.
    # Compute OPTICS
    clust = OPTICS(max_eps=5.0 * 6.0, min_samples=4, xi=0.1, metric=metric)
    clust.fit(csr_container(X) if csr_container is not None else X)
    # number of clusters, ignoring noise if present
    n_clusters_1 = len(set(clust.labels_)) - int(-1 in clust.labels_)
    assert n_clusters_1 == n_clusters

    # check attribute types and sizes
    assert clust.labels_.shape == (len(X),)
    assert clust.labels_.dtype.kind == "i"

    assert clust.reachability_.shape == (len(X),)
    assert clust.reachability_.dtype.kind == "f"

    assert clust.core_distances_.shape == (len(X),)
    assert clust.core_distances_.dtype.kind == "f"

    assert clust.ordering_.shape == (len(X),)
    assert clust.ordering_.dtype.kind == "i"
    assert set(clust.ordering_) == set(range(len(X)))