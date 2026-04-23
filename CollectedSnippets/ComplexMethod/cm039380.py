def test_criterion_copy():
    # Let's check whether copy of our criterion has the same type
    # and properties as original
    n_outputs = 3
    n_classes = np.arange(3, dtype=np.intp)
    n_samples = 100

    def _pickle_copy(obj):
        return pickle.loads(pickle.dumps(obj))

    for copy_func in [copy.copy, copy.deepcopy, _pickle_copy]:
        for _, typename in CRITERIA_CLF.items():
            criteria = typename(n_outputs, n_classes)
            result = copy_func(criteria).__reduce__()
            typename_, (n_outputs_, n_classes_), _ = result
            assert typename == typename_
            assert n_outputs == n_outputs_
            assert_array_equal(n_classes, n_classes_)

        for _, typename in CRITERIA_REG.items():
            criteria = typename(n_outputs, n_samples)
            result = copy_func(criteria).__reduce__()
            typename_, (n_outputs_, n_samples_), _ = result
            assert typename == typename_
            assert n_outputs == n_outputs_
            assert n_samples == n_samples_