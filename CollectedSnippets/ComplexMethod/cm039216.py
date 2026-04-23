def test_20news(fetch_20newsgroups_fxt):
    data = fetch_20newsgroups_fxt(subset="all", shuffle=False)
    assert data.DESCR.startswith(".. _20newsgroups_dataset:")

    # Extract a reduced dataset
    data2cats = fetch_20newsgroups_fxt(
        subset="all", categories=data.target_names[-1:-3:-1], shuffle=False
    )
    # Check that the ordering of the target_names is the same
    # as the ordering in the full dataset
    assert data2cats.target_names == data.target_names[-2:]
    # Assert that we have only 0 and 1 as labels
    assert np.unique(data2cats.target).tolist() == [0, 1]

    # Check that the number of filenames is consistent with data/target
    assert len(data2cats.filenames) == len(data2cats.target)
    assert len(data2cats.filenames) == len(data2cats.data)

    # Check that the first entry of the reduced dataset corresponds to
    # the first entry of the corresponding category in the full dataset
    entry1 = data2cats.data[0]
    category = data2cats.target_names[data2cats.target[0]]
    label = data.target_names.index(category)
    entry2 = data.data[np.where(data.target == label)[0][0]]
    assert entry1 == entry2

    # check that return_X_y option
    X, y = fetch_20newsgroups_fxt(subset="all", shuffle=False, return_X_y=True)
    assert len(X) == len(data.data)
    assert y.shape == data.target.shape