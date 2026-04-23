def _check_average_precision(display, constructor_name, pos_label):
        if pos_label == "cancer":
            avg_prec_limit = 0.6338
            avg_prec_limit_multi = [0.8189, 0.8802, 0.8795]
        else:
            avg_prec_limit = 0.9953
            avg_prec_limit_multi = [0.9966, 0.9984, 0.9976]

        def average_precision_uninterpolated(precision, recall):
            return -np.sum(np.diff(recall) * np.array(precision)[:-1])

        if constructor_name == "from_cv_results":
            for idx, average_precision in enumerate(display.average_precision):
                assert average_precision == pytest.approx(
                    avg_prec_limit_multi[idx], rel=1e-3
                )
                assert average_precision_uninterpolated(
                    display.precision[idx], display.recall[idx]
                ) == pytest.approx(avg_prec_limit_multi[idx], rel=1e-3)
        else:
            assert display.average_precision == pytest.approx(avg_prec_limit, rel=1e-3)
            assert average_precision_uninterpolated(
                display.precision, display.recall
            ) == pytest.approx(avg_prec_limit, rel=1e-3)