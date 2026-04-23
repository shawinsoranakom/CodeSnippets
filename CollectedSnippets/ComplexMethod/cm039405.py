def test_verbose(init_name, capsys):
    # assert there is proper output when verbose = 1, for every initialization
    # except auto because auto will call one of the others
    rng = np.random.RandomState(42)
    X, y = make_blobs(n_samples=30, centers=6, n_features=5, random_state=0)
    regexp_init = r"... done in \ *\d+\.\d{2}s"
    msgs = {
        "pca": "Finding principal components" + regexp_init,
        "lda": "Finding most discriminative components" + regexp_init,
    }
    if init_name == "precomputed":
        init = rng.randn(X.shape[1], X.shape[1])
    else:
        init = init_name
    nca = NeighborhoodComponentsAnalysis(verbose=1, init=init)
    nca.fit(X, y)
    out, _ = capsys.readouterr()

    # check output
    lines = re.split("\n+", out)
    # if pca or lda init, an additional line is printed, so we test
    # it and remove it to test the rest equally among initializations
    if init_name in ["pca", "lda"]:
        assert re.match(msgs[init_name], lines[0])
        lines = lines[1:]
    assert lines[0] == "[NeighborhoodComponentsAnalysis]"
    header = "{:>10} {:>20} {:>10}".format("Iteration", "Objective Value", "Time(s)")
    assert lines[1] == "[NeighborhoodComponentsAnalysis] {}".format(header)
    assert lines[2] == "[NeighborhoodComponentsAnalysis] {}".format("-" * len(header))
    for line in lines[3:-2]:
        # The following regex will match for instance:
        # '[NeighborhoodComponentsAnalysis]  0    6.988936e+01   0.01'
        assert re.match(
            r"\[NeighborhoodComponentsAnalysis\] *\d+ *\d\.\d{6}e"
            r"[+|-]\d+\ *\d+\.\d{2}",
            line,
        )
    assert re.match(
        r"\[NeighborhoodComponentsAnalysis\] Training took\ *\d+\.\d{2}s\.",
        lines[-2],
    )
    assert lines[-1] == ""