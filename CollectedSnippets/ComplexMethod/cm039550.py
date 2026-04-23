def test_classification_report_dictionary_output():
    # Test performance report with dictionary output
    iris = datasets.load_iris()
    y_true, y_pred, _ = make_prediction(dataset=iris, binary=False)

    # print classification report with class names
    expected_report = {
        "setosa": {
            "precision": 0.82608695652173914,
            "recall": 0.79166666666666663,
            "f1-score": 0.8085106382978724,
            "support": 24,
        },
        "versicolor": {
            "precision": 0.33333333333333331,
            "recall": 0.096774193548387094,
            "f1-score": 0.15000000000000002,
            "support": 31,
        },
        "virginica": {
            "precision": 0.41860465116279072,
            "recall": 0.90000000000000002,
            "f1-score": 0.57142857142857151,
            "support": 20,
        },
        "macro avg": {
            "f1-score": 0.5099797365754813,
            "precision": 0.5260083136726211,
            "recall": 0.596146953405018,
            "support": 75,
        },
        "accuracy": 0.5333333333333333,
        "weighted avg": {
            "f1-score": 0.47310435663627154,
            "precision": 0.5137535108414785,
            "recall": 0.5333333333333333,
            "support": 75,
        },
    }

    report = classification_report(
        y_true,
        y_pred,
        labels=np.arange(len(iris.target_names)),
        target_names=iris.target_names,
        output_dict=True,
    )

    # assert the 2 dicts are equal.
    assert report.keys() == expected_report.keys()
    for key in expected_report:
        if key == "accuracy":
            assert isinstance(report[key], float)
            assert report[key] == expected_report[key]
        else:
            assert report[key].keys() == expected_report[key].keys()
            for metric in expected_report[key]:
                assert_almost_equal(expected_report[key][metric], report[key][metric])

    assert isinstance(expected_report["setosa"]["precision"], float)
    assert isinstance(expected_report["macro avg"]["precision"], float)
    assert isinstance(expected_report["setosa"]["support"], int)
    assert isinstance(expected_report["macro avg"]["support"], int)