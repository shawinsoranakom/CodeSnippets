def test_set_order_dense(order, input_order):
    """Check that _set_order returns arrays with promised order."""
    X = np.array([[0], [0], [0]], order=input_order)
    y = np.array([0, 0, 0], order=input_order)
    X2, y2 = _set_order(X, y, order=order)
    if order == "C":
        assert X2.flags["C_CONTIGUOUS"]
        assert y2.flags["C_CONTIGUOUS"]
    elif order == "F":
        assert X2.flags["F_CONTIGUOUS"]
        assert y2.flags["F_CONTIGUOUS"]

    if order == input_order:
        assert X is X2
        assert y is y2