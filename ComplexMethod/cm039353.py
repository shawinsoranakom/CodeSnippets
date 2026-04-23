def test_gradient_descent_stops(capsys):
    # Test stopping conditions of gradient descent.
    class ObjectiveSmallGradient:
        def __init__(self):
            self.it = -1

        def __call__(self, _, compute_error=True):
            self.it += 1
            return (10 - self.it) / 10.0, np.array([1e-5])

    def flat_function(_, compute_error=True):
        return 0.0, np.ones(1)

    # Gradient norm
    _, error, it = _gradient_descent(
        ObjectiveSmallGradient(),
        np.zeros(1),
        0,
        max_iter=100,
        n_iter_without_progress=100,
        momentum=0.0,
        learning_rate=0.0,
        min_gain=0.0,
        min_grad_norm=1e-5,
        verbose=2,
    )
    assert error == 1.0
    assert it == 0
    assert "gradient norm" in capsys.readouterr().out

    # Maximum number of iterations without improvement
    _, error, it = _gradient_descent(
        flat_function,
        np.zeros(1),
        0,
        max_iter=100,
        n_iter_without_progress=10,
        momentum=0.0,
        learning_rate=0.0,
        min_gain=0.0,
        min_grad_norm=0.0,
        verbose=2,
    )
    assert error == 0.0
    assert it == 11
    assert "did not make any progress" in capsys.readouterr().out

    # Maximum number of iterations
    _, error, it = _gradient_descent(
        ObjectiveSmallGradient(),
        np.zeros(1),
        0,
        max_iter=11,
        n_iter_without_progress=100,
        momentum=0.0,
        learning_rate=0.0,
        min_gain=0.0,
        min_grad_norm=0.0,
        verbose=2,
    )
    assert error == 0.0
    assert it == 10
    assert "Iteration 10" in capsys.readouterr().out