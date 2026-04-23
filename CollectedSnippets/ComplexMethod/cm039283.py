def test_tfidf_vectorizer_setters():
    norm, use_idf, smooth_idf, sublinear_tf = "l2", False, False, False
    tv = TfidfVectorizer(
        norm=norm, use_idf=use_idf, smooth_idf=smooth_idf, sublinear_tf=sublinear_tf
    )
    tv.fit(JUNK_FOOD_DOCS)
    assert tv._tfidf.norm == norm
    assert tv._tfidf.use_idf == use_idf
    assert tv._tfidf.smooth_idf == smooth_idf
    assert tv._tfidf.sublinear_tf == sublinear_tf

    # assigning value to `TfidfTransformer` should not have any effect until
    # fitting
    tv.norm = "l1"
    tv.use_idf = True
    tv.smooth_idf = True
    tv.sublinear_tf = True
    assert tv._tfidf.norm == norm
    assert tv._tfidf.use_idf == use_idf
    assert tv._tfidf.smooth_idf == smooth_idf
    assert tv._tfidf.sublinear_tf == sublinear_tf

    tv.fit(JUNK_FOOD_DOCS)
    assert tv._tfidf.norm == tv.norm
    assert tv._tfidf.use_idf == tv.use_idf
    assert tv._tfidf.smooth_idf == tv.smooth_idf
    assert tv._tfidf.sublinear_tf == tv.sublinear_tf