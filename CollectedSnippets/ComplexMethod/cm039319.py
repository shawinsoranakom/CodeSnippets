def conduct_test(base_clf, test_predict_proba=False):
        clf = OneVsRestClassifier(base_clf).fit(X, y)
        assert set(clf.classes_) == classes
        y_pred = clf.predict(np.array([[0, 0, 4]]))[0]
        assert_array_equal(y_pred, ["eggs"])
        if hasattr(base_clf, "decision_function"):
            dec = clf.decision_function(X)
            assert dec.shape == (5,)

        if test_predict_proba:
            X_test = np.array([[0, 0, 4]])
            probabilities = clf.predict_proba(X_test)
            assert 2 == len(probabilities[0])
            assert clf.classes_[np.argmax(probabilities, axis=1)] == clf.predict(X_test)

        # test input as label indicator matrix
        clf = OneVsRestClassifier(base_clf).fit(X, Y)
        y_pred = clf.predict([[3, 0, 0]])[0]
        assert y_pred == 1