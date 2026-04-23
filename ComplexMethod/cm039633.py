def test_sgd_predict_proba_method_access(klass):
    # Checks that SGDClassifier predict_proba and predict_log_proba methods
    # can either be accessed or raise an appropriate error message
    # otherwise. See
    # https://github.com/scikit-learn/scikit-learn/issues/10938 for more
    # details.
    for loss in linear_model.SGDClassifier.loss_functions:
        clf = SGDClassifier(loss=loss)
        if loss in ("log_loss", "modified_huber"):
            assert hasattr(clf, "predict_proba")
            assert hasattr(clf, "predict_log_proba")
        else:
            inner_msg = "probability estimates are not available for loss={!r}".format(
                loss
            )
            assert not hasattr(clf, "predict_proba")
            assert not hasattr(clf, "predict_log_proba")
            with pytest.raises(
                AttributeError, match="has no attribute 'predict_proba'"
            ) as exec_info:
                clf.predict_proba

            assert isinstance(exec_info.value.__cause__, AttributeError)
            assert inner_msg in str(exec_info.value.__cause__)

            with pytest.raises(
                AttributeError, match="has no attribute 'predict_log_proba'"
            ) as exec_info:
                clf.predict_log_proba
            assert isinstance(exec_info.value.__cause__, AttributeError)
            assert inner_msg in str(exec_info.value.__cause__)