def test_independent_shape(self):
        for Dist, params in _get_examples():
            for param in params:
                base_dist = Dist(**param)
                x = base_dist.sample()
                base_log_prob_shape = base_dist.log_prob(x).shape
                for reinterpreted_batch_ndims in range(len(base_dist.batch_shape) + 1):
                    indep_dist = Independent(base_dist, reinterpreted_batch_ndims)
                    indep_log_prob_shape = base_log_prob_shape[
                        : len(base_log_prob_shape) - reinterpreted_batch_ndims
                    ]
                    self.assertEqual(indep_dist.log_prob(x).shape, indep_log_prob_shape)
                    self.assertEqual(
                        indep_dist.sample().shape, base_dist.sample().shape
                    )
                    self.assertEqual(indep_dist.has_rsample, base_dist.has_rsample)
                    if indep_dist.has_rsample:
                        self.assertEqual(
                            indep_dist.sample().shape, base_dist.sample().shape
                        )
                    try:
                        self.assertEqual(
                            indep_dist.enumerate_support().shape,
                            base_dist.enumerate_support().shape,
                        )
                        self.assertEqual(indep_dist.mean.shape, base_dist.mean.shape)
                    except NotImplementedError:
                        pass
                    try:
                        self.assertEqual(
                            indep_dist.variance.shape, base_dist.variance.shape
                        )
                    except NotImplementedError:
                        pass
                    try:
                        self.assertEqual(
                            indep_dist.entropy().shape, indep_log_prob_shape
                        )
                    except NotImplementedError:
                        pass