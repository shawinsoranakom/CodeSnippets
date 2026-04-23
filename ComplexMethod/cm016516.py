def is_equal(x, y):
    if torch.is_tensor(x) and torch.is_tensor(y):
        return torch.equal(x, y)
    elif isinstance(x, dict) and isinstance(y, dict):
        if x.keys() != y.keys():
            return False
        return all(is_equal(x[k], y[k]) for k in x)
    elif isinstance(x, (list, tuple)) and isinstance(y, (list, tuple)):
        if type(x) is not type(y) or len(x) != len(y):
            return False
        return all(is_equal(a, b) for a, b in zip(x, y))
    else:
        try:
            return x == y
        except Exception:
            logging.warning("comparison issue with COND")
            return False