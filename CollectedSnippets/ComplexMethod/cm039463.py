def test_base():
    # Check BaseEnsemble methods.
    ensemble = BaggingClassifier(
        estimator=Perceptron(random_state=None), n_estimators=3
    )

    iris = load_iris()
    ensemble.fit(iris.data, iris.target)
    ensemble.estimators_ = []  # empty the list and create estimators manually

    ensemble._make_estimator()
    random_state = np.random.RandomState(3)
    ensemble._make_estimator(random_state=random_state)
    ensemble._make_estimator(random_state=random_state)
    ensemble._make_estimator(append=False)

    assert 3 == len(ensemble)
    assert 3 == len(ensemble.estimators_)

    assert isinstance(ensemble[0], Perceptron)
    assert ensemble[0].random_state is None
    assert isinstance(ensemble[1].random_state, int)
    assert isinstance(ensemble[2].random_state, int)
    assert ensemble[1].random_state != ensemble[2].random_state

    np_int_ensemble = BaggingClassifier(
        estimator=Perceptron(), n_estimators=np.int32(3)
    )
    np_int_ensemble.fit(iris.data, iris.target)