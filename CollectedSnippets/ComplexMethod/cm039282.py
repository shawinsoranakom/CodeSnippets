def test_vectorizer():
    # raw documents as an iterator
    train_data = iter(ALL_FOOD_DOCS[:-1])
    test_data = [ALL_FOOD_DOCS[-1]]
    n_train = len(ALL_FOOD_DOCS) - 1

    # test without vocabulary
    v1 = CountVectorizer(max_df=0.5)
    counts_train = v1.fit_transform(train_data)
    if hasattr(counts_train, "tocsr"):
        counts_train = counts_train.tocsr()
    assert counts_train[0, v1.vocabulary_["pizza"]] == 2

    # build a vectorizer v1 with the same vocabulary as the one fitted by v1
    v2 = CountVectorizer(vocabulary=v1.vocabulary_)

    # compare that the two vectorizer give the same output on the test sample
    for v in (v1, v2):
        counts_test = v.transform(test_data)
        if hasattr(counts_test, "tocsr"):
            counts_test = counts_test.tocsr()

        vocabulary = v.vocabulary_
        assert counts_test[0, vocabulary["salad"]] == 1
        assert counts_test[0, vocabulary["tomato"]] == 1
        assert counts_test[0, vocabulary["water"]] == 1

        # stop word from the fixed list
        assert "the" not in vocabulary

        # stop word found automatically by the vectorizer DF thresholding
        # words that are high frequent across the complete corpus are likely
        # to be not informative (either real stop words of extraction
        # artifacts)
        assert "copyright" not in vocabulary

        # not present in the sample
        assert counts_test[0, vocabulary["coke"]] == 0
        assert counts_test[0, vocabulary["burger"]] == 0
        assert counts_test[0, vocabulary["beer"]] == 0
        assert counts_test[0, vocabulary["pizza"]] == 0

    # test tf-idf
    t1 = TfidfTransformer(norm="l1")
    tfidf = t1.fit(counts_train).transform(counts_train).toarray()
    assert len(t1.idf_) == len(v1.vocabulary_)
    assert tfidf.shape == (n_train, len(v1.vocabulary_))

    # test tf-idf with new data
    tfidf_test = t1.transform(counts_test).toarray()
    assert tfidf_test.shape == (len(test_data), len(v1.vocabulary_))

    # test tf alone
    t2 = TfidfTransformer(norm="l1", use_idf=False)
    tf = t2.fit(counts_train).transform(counts_train).toarray()
    assert not hasattr(t2, "idf_")

    # test idf transform with unlearned idf vector
    t3 = TfidfTransformer(use_idf=True)
    with pytest.raises(ValueError):
        t3.transform(counts_train)

    # L1-normalized term frequencies sum to one
    assert_array_almost_equal(np.sum(tf, axis=1), [1.0] * n_train)

    # test the direct tfidf vectorizer
    # (equivalent to term count vectorizer + tfidf transformer)
    train_data = iter(ALL_FOOD_DOCS[:-1])
    tv = TfidfVectorizer(norm="l1")

    tv.max_df = v1.max_df
    tfidf2 = tv.fit_transform(train_data).toarray()
    assert not tv.fixed_vocabulary_
    assert_array_almost_equal(tfidf, tfidf2)

    # test the direct tfidf vectorizer with new data
    tfidf_test2 = tv.transform(test_data).toarray()
    assert_array_almost_equal(tfidf_test, tfidf_test2)

    # test transform on unfitted vectorizer with empty vocabulary
    v3 = CountVectorizer(vocabulary=None)
    with pytest.raises(ValueError):
        v3.transform(train_data)

    # ascii preprocessor?
    v3.set_params(strip_accents="ascii", lowercase=False)
    processor = v3.build_preprocessor()
    text = "J'ai mangé du kangourou  ce midi, c'était pas très bon."
    expected = strip_accents_ascii(text)
    result = processor(text)
    assert expected == result

    # error on bad strip_accents param
    v3.set_params(strip_accents="_gabbledegook_", preprocessor=None)
    with pytest.raises(ValueError):
        v3.build_preprocessor()

    # error with bad analyzer type
    v3.set_params = "_invalid_analyzer_type_"
    with pytest.raises(ValueError):
        v3.build_analyzer()