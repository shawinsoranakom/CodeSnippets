def kmeans(
    data, k, initial_centroids, maxiter=500, record_heterogeneity=None, verbose=False
):
    """Runs k-means on given data and initial set of centroids.
    maxiter: maximum number of iterations to run.(default=500)
    record_heterogeneity: (optional) a list, to store the history of heterogeneity
                          as function of iterations
                          if None, do not store the history.
    verbose: if True, print how many data points changed their cluster labels in
                          each iteration"""
    centroids = initial_centroids[:]
    prev_cluster_assignment = None

    for itr in range(maxiter):
        if verbose:
            print(itr, end="")

        # 1. Make cluster assignments using nearest centroids
        cluster_assignment = assign_clusters(data, centroids)

        # 2. Compute a new centroid for each of the k clusters, averaging all data
        #    points assigned to that cluster.
        centroids = revise_centroids(data, k, cluster_assignment)

        # Check for convergence: if none of the assignments changed, stop
        if (
            prev_cluster_assignment is not None
            and (prev_cluster_assignment == cluster_assignment).all()
        ):
            break

        # Print number of new assignments
        if prev_cluster_assignment is not None:
            num_changed = np.sum(prev_cluster_assignment != cluster_assignment)
            if verbose:
                print(
                    f"    {num_changed:5d} elements changed their cluster assignment."
                )

        # Record heterogeneity convergence metric
        if record_heterogeneity is not None:
            # YOUR CODE HERE
            score = compute_heterogeneity(data, k, centroids, cluster_assignment)
            record_heterogeneity.append(score)

        prev_cluster_assignment = cluster_assignment[:]

    return centroids, cluster_assignment