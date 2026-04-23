def split_next(self):
        """Split the node with highest potential gain.

        Returns
        -------
        left : TreeNode
            The resulting left child.
        right : TreeNode
            The resulting right child.
        """
        # Consider the node with the highest loss reduction (a.k.a. gain)
        node = heappop(self.splittable_nodes)

        tic = time()
        (
            sample_indices_left,
            sample_indices_right,
            right_child_pos,
        ) = self.splitter.split_indices(node.split_info, node.sample_indices)
        self.total_apply_split_time += time() - tic

        depth = node.depth + 1
        n_leaf_nodes = len(self.finalized_leaves) + len(self.splittable_nodes)
        n_leaf_nodes += 2

        left_child_node = TreeNode(
            depth=depth,
            sample_indices=sample_indices_left,
            partition_start=node.partition_start,
            partition_stop=node.partition_start + right_child_pos,
            sum_gradients=node.split_info.sum_gradient_left,
            sum_hessians=node.split_info.sum_hessian_left,
            value=node.split_info.value_left,
        )
        right_child_node = TreeNode(
            depth=depth,
            sample_indices=sample_indices_right,
            partition_start=left_child_node.partition_stop,
            partition_stop=node.partition_stop,
            sum_gradients=node.split_info.sum_gradient_right,
            sum_hessians=node.split_info.sum_hessian_right,
            value=node.split_info.value_right,
        )

        node.right_child = right_child_node
        node.left_child = left_child_node

        # set interaction constraints (the indices of the constraints sets)
        if self.interaction_cst is not None:
            # Calculate allowed_features and interaction_cst_indices only once. Child
            # nodes inherit them before they get split.
            (
                left_child_node.allowed_features,
                left_child_node.interaction_cst_indices,
            ) = self._compute_interactions(node)
            right_child_node.interaction_cst_indices = (
                left_child_node.interaction_cst_indices
            )
            right_child_node.allowed_features = left_child_node.allowed_features

        if not self.has_missing_values[node.split_info.feature_idx]:
            # If no missing values are encountered at fit time, then samples
            # with missing values during predict() will go to whichever child
            # has the most samples.
            node.split_info.missing_go_to_left = (
                left_child_node.n_samples > right_child_node.n_samples
            )

        self.n_nodes += 2
        self.n_categorical_splits += node.split_info.is_categorical

        if self.max_leaf_nodes is not None and n_leaf_nodes == self.max_leaf_nodes:
            self._finalize_leaf(left_child_node)
            self._finalize_leaf(right_child_node)
            self._finalize_splittable_nodes()
            return left_child_node, right_child_node

        if self.max_depth is not None and depth == self.max_depth:
            self._finalize_leaf(left_child_node)
            self._finalize_leaf(right_child_node)
            return left_child_node, right_child_node

        if left_child_node.n_samples < self.min_samples_leaf * 2:
            self._finalize_leaf(left_child_node)
        if right_child_node.n_samples < self.min_samples_leaf * 2:
            self._finalize_leaf(right_child_node)

        if self.with_monotonic_cst:
            # Set value bounds for respecting monotonic constraints
            # See test_nodes_values() for details
            if (
                self.monotonic_cst[node.split_info.feature_idx]
                == MonotonicConstraint.NO_CST
            ):
                lower_left = lower_right = node.children_lower_bound
                upper_left = upper_right = node.children_upper_bound
            else:
                mid = (left_child_node.value + right_child_node.value) / 2
                if (
                    self.monotonic_cst[node.split_info.feature_idx]
                    == MonotonicConstraint.POS
                ):
                    lower_left, upper_left = node.children_lower_bound, mid
                    lower_right, upper_right = mid, node.children_upper_bound
                else:  # NEG
                    lower_left, upper_left = mid, node.children_upper_bound
                    lower_right, upper_right = node.children_lower_bound, mid
            left_child_node.set_children_bounds(lower_left, upper_left)
            right_child_node.set_children_bounds(lower_right, upper_right)

        # Compute histograms of children, and compute their best possible split
        # (if needed)
        should_split_left = not left_child_node.is_leaf
        should_split_right = not right_child_node.is_leaf
        if should_split_left or should_split_right:
            # We will compute the histograms of both nodes even if one of them
            # is a leaf, since computing the second histogram is very cheap
            # (using histogram subtraction).
            n_samples_left = left_child_node.sample_indices.shape[0]
            n_samples_right = right_child_node.sample_indices.shape[0]
            if n_samples_left < n_samples_right:
                smallest_child = left_child_node
                largest_child = right_child_node
            else:
                smallest_child = right_child_node
                largest_child = left_child_node

            # We use the brute O(n_samples) method on the child that has the
            # smallest number of samples, and the subtraction trick O(n_bins)
            # on the other one.
            # Note that both left and right child have the same allowed_features.
            tic = time()
            smallest_child.histograms = self.histogram_builder.compute_histograms_brute(
                smallest_child.sample_indices, smallest_child.allowed_features
            )
            largest_child.histograms = (
                self.histogram_builder.compute_histograms_subtraction(
                    node.histograms,
                    smallest_child.histograms,
                    smallest_child.allowed_features,
                )
            )
            # node.histograms is reused in largest_child.histograms. To break cyclic
            # memory references and help garbage collection, we set it to None.
            node.histograms = None
            self.total_compute_hist_time += time() - tic

            tic = time()
            if should_split_left:
                self._compute_best_split_and_push(left_child_node)
            if should_split_right:
                self._compute_best_split_and_push(right_child_node)
            self.total_find_split_time += time() - tic

            # Release memory used by histograms as they are no longer needed
            # for leaf nodes since they won't be split.
            for child in (left_child_node, right_child_node):
                if child.is_leaf:
                    del child.histograms

        # Release memory used by histograms as they are no longer needed for
        # internal nodes once children histograms have been computed.
        del node.histograms

        return left_child_node, right_child_node