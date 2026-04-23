def test_check_accuracy_on_digits():
    # Non regression test to make sure that any further refactoring / optim
    # of the NB models do not harm the performance on a slightly non-linearly
    # separable dataset
    X, y = load_digits(return_X_y=True)
    binary_3v8 = np.logical_or(y == 3, y == 8)
    X_3v8, y_3v8 = X[binary_3v8], y[binary_3v8]

    # Multinomial NB
    scores = cross_val_score(MultinomialNB(alpha=10), X, y, cv=10)
    assert scores.mean() > 0.86

    scores = cross_val_score(MultinomialNB(alpha=10), X_3v8, y_3v8, cv=10)
    assert scores.mean() > 0.94

    # Bernoulli NB
    scores = cross_val_score(BernoulliNB(alpha=10), X > 4, y, cv=10)
    assert scores.mean() > 0.83

    scores = cross_val_score(BernoulliNB(alpha=10), X_3v8 > 4, y_3v8, cv=10)
    assert scores.mean() > 0.92

    # Gaussian NB
    scores = cross_val_score(GaussianNB(), X, y, cv=10)
    assert scores.mean() > 0.77

    scores = cross_val_score(GaussianNB(var_smoothing=0.1), X, y, cv=10)
    assert scores.mean() > 0.89

    scores = cross_val_score(GaussianNB(), X_3v8, y_3v8, cv=10)
    assert scores.mean() > 0.86