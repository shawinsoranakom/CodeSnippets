def test_fastica_simple(add_noise, global_random_seed, global_dtype):
    if (
        global_random_seed == 20
        and global_dtype == np.float32
        and not add_noise
        and os.getenv("DISTRIB") == "ubuntu"
    ):
        pytest.xfail(
            "FastICA instability with Ubuntu Atlas build with float32 "
            "global_dtype. For more details, see "
            "https://github.com/scikit-learn/scikit-learn/issues/24131#issuecomment-1208091119"
        )

    # Test the FastICA algorithm on very simple data.
    rng = np.random.RandomState(global_random_seed)
    n_samples = 1000
    # Generate two sources:
    s1 = (2 * np.sin(np.linspace(0, 100, n_samples)) > 0) - 1
    s2 = stats.t.rvs(1, size=n_samples, random_state=global_random_seed)
    s = np.c_[s1, s2].T
    center_and_norm(s)
    s = s.astype(global_dtype)
    s1, s2 = s

    # Mixing angle
    phi = 0.6
    mixing = np.array([[np.cos(phi), np.sin(phi)], [np.sin(phi), -np.cos(phi)]])
    mixing = mixing.astype(global_dtype)
    m = np.dot(mixing, s)

    if add_noise:
        m += 0.1 * rng.randn(2, 1000)

    center_and_norm(m)

    # function as fun arg
    def g_test(x):
        return x**3, (3 * x**2).mean(axis=-1)

    algos = ["parallel", "deflation"]
    nls = ["logcosh", "exp", "cube", g_test]
    whitening = ["arbitrary-variance", "unit-variance", False]
    for algo, nl, whiten in itertools.product(algos, nls, whitening):
        if whiten:
            k_, mixing_, s_ = fastica(
                m.T, fun=nl, whiten=whiten, algorithm=algo, random_state=rng
            )
            with pytest.raises(ValueError):
                fastica(m.T, fun=np.tanh, whiten=whiten, algorithm=algo)
        else:
            pca = PCA(n_components=2, whiten=True, random_state=rng)
            X = pca.fit_transform(m.T)
            k_, mixing_, s_ = fastica(
                X, fun=nl, algorithm=algo, whiten=False, random_state=rng
            )
            with pytest.raises(ValueError):
                fastica(X, fun=np.tanh, algorithm=algo)
        s_ = s_.T
        # Check that the mixing model described in the docstring holds:
        if whiten:
            # XXX: exact reconstruction to standard relative tolerance is not
            # possible. This is probably expected when add_noise is True but we
            # also need a non-trivial atol in float32 when add_noise is False.
            #
            # Note that the 2 sources are non-Gaussian in this test.
            atol = 1e-5 if global_dtype == np.float32 else 0
            assert_allclose(np.dot(np.dot(mixing_, k_), m), s_, atol=atol)

        center_and_norm(s_)
        s1_, s2_ = s_
        # Check to see if the sources have been estimated
        # in the wrong order
        if abs(np.dot(s1_, s2)) > abs(np.dot(s1_, s1)):
            s2_, s1_ = s_
        s1_ *= np.sign(np.dot(s1_, s1))
        s2_ *= np.sign(np.dot(s2_, s2))

        # Check that we have estimated the original sources
        if not add_noise:
            assert_allclose(np.dot(s1_, s1) / n_samples, 1, atol=1e-2)
            assert_allclose(np.dot(s2_, s2) / n_samples, 1, atol=1e-2)
        else:
            assert_allclose(np.dot(s1_, s1) / n_samples, 1, atol=1e-1)
            assert_allclose(np.dot(s2_, s2) / n_samples, 1, atol=1e-1)

    # Test FastICA class
    _, _, sources_fun = fastica(
        m.T, fun=nl, algorithm=algo, random_state=global_random_seed
    )
    ica = FastICA(fun=nl, algorithm=algo, random_state=global_random_seed)
    sources = ica.fit_transform(m.T)
    assert ica.components_.shape == (2, 2)
    assert sources.shape == (1000, 2)

    assert_allclose(sources_fun, sources)
    # Set atol to account for the different magnitudes of the elements in sources
    # (from 1e-4 to 1e1).
    atol = np.max(np.abs(sources)) * (1e-5 if global_dtype == np.float32 else 1e-7)
    assert_allclose(sources, ica.transform(m.T), atol=atol)

    assert ica.mixing_.shape == (2, 2)

    ica = FastICA(fun=np.tanh, algorithm=algo)
    with pytest.raises(ValueError):
        ica.fit(m.T)