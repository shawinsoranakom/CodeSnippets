def _run_search(self, evaluate_candidates):
        candidate_params = self._generate_candidate_params()

        if self.resource != "n_samples" and any(
            self.resource in candidate for candidate in candidate_params
        ):
            # Can only check this now since we need the candidates list
            raise ValueError(
                f"Cannot use parameter {self.resource} as the resource since "
                "it is part of the searched parameters."
            )

        # n_required_iterations is the number of iterations needed so that the
        # last iterations evaluates less than `factor` candidates.
        n_required_iterations = 1 + floor(log(len(candidate_params), self.factor))

        if self.min_resources == "exhaust":
            # To exhaust the resources, we want to start with the biggest
            # min_resources possible so that the last (required) iteration
            # uses as many resources as possible
            last_iteration = n_required_iterations - 1
            self.min_resources_ = max(
                self.min_resources_,
                self.max_resources_ // self.factor**last_iteration,
            )

        # n_possible_iterations is the number of iterations that we can
        # actually do starting from min_resources and without exceeding
        # max_resources. Depending on max_resources and the number of
        # candidates, this may be higher or smaller than
        # n_required_iterations.
        n_possible_iterations = 1 + floor(
            log(self.max_resources_ // self.min_resources_, self.factor)
        )

        if self.aggressive_elimination:
            n_iterations = n_required_iterations
        else:
            n_iterations = min(n_possible_iterations, n_required_iterations)

        if self.verbose:
            print(f"n_iterations: {n_iterations}")
            print(f"n_required_iterations: {n_required_iterations}")
            print(f"n_possible_iterations: {n_possible_iterations}")
            print(f"min_resources_: {self.min_resources_}")
            print(f"max_resources_: {self.max_resources_}")
            print(f"aggressive_elimination: {self.aggressive_elimination}")
            print(f"factor: {self.factor}")

        self.n_resources_ = []
        self.n_candidates_ = []

        for itr in range(n_iterations):
            power = itr  # default
            if self.aggressive_elimination:
                # this will set n_resources to the initial value (i.e. the
                # value of n_resources at the first iteration) for as many
                # iterations as needed (while candidates are being
                # eliminated), and then go on as usual.
                power = max(0, itr - n_required_iterations + n_possible_iterations)

            n_resources = int(self.factor**power * self.min_resources_)
            # guard, probably not needed
            n_resources = min(n_resources, self.max_resources_)
            self.n_resources_.append(n_resources)

            n_candidates = len(candidate_params)
            self.n_candidates_.append(n_candidates)

            if self.verbose:
                print("-" * 10)
                print(f"iter: {itr}")
                print(f"n_candidates: {n_candidates}")
                print(f"n_resources: {n_resources}")

            if self.resource == "n_samples":
                # subsampling will be done in cv.split()
                cv = _SubsampleMetaSplitter(
                    base_cv=self._checked_cv_orig,
                    fraction=n_resources / self._n_samples_orig,
                    subsample_test=True,
                    random_state=self.random_state,
                )

            else:
                # Need copy so that the n_resources of next iteration does
                # not overwrite
                candidate_params = [c.copy() for c in candidate_params]
                for candidate in candidate_params:
                    candidate[self.resource] = n_resources
                cv = self._checked_cv_orig

            more_results = {
                "iter": [itr] * n_candidates,
                "n_resources": [n_resources] * n_candidates,
            }

            results = evaluate_candidates(
                candidate_params, cv, more_results=more_results
            )

            n_candidates_to_keep = ceil(n_candidates / self.factor)
            candidate_params = _top_k(results, n_candidates_to_keep, itr)

        self.n_remaining_candidates_ = len(candidate_params)
        self.n_required_iterations_ = n_required_iterations
        self.n_possible_iterations_ = n_possible_iterations
        self.n_iterations_ = n_iterations