def _print_iteration_stats(self, iteration_start_time):
        """Print info about the current fitting iteration."""
        log_msg = ""

        predictors_of_ith_iteration = [
            predictors_list
            for predictors_list in self._predictors[-1]
            if predictors_list
        ]
        n_trees = len(predictors_of_ith_iteration)
        max_depth = max(
            predictor.get_max_depth() for predictor in predictors_of_ith_iteration
        )
        n_leaves = sum(
            predictor.get_n_leaf_nodes() for predictor in predictors_of_ith_iteration
        )

        if n_trees == 1:
            log_msg += "{} tree, {} leaves, ".format(n_trees, n_leaves)
        else:
            log_msg += "{} trees, {} leaves ".format(n_trees, n_leaves)
            log_msg += "({} on avg), ".format(int(n_leaves / n_trees))

        log_msg += "max depth = {}, ".format(max_depth)

        if self.do_early_stopping_:
            if self.scoring == "loss":
                factor = -1  # score_ arrays contain the negative loss
                name = "loss"
            else:
                factor = 1
                name = "score"
            log_msg += "train {}: {:.5f}, ".format(name, factor * self.train_score_[-1])
            if self._use_validation_data:
                log_msg += "val {}: {:.5f}, ".format(
                    name, factor * self.validation_score_[-1]
                )

        iteration_time = time() - iteration_start_time
        log_msg += "in {:0.3f}s".format(iteration_time)

        print(log_msg)