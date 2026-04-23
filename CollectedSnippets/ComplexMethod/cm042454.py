def is_column(x):
    if isinstance(x, np.ndarray):
        if x.ndim == 1:
            return True
        elif x.ndim == 2 and x.shape[1] == 1:
            return True
        else:
            return False
    elif isinstance(x, (MX, SX, DM)):
        if x.shape[1] == 1:
            return True
        elif x.shape[0] == 0 and x.shape[1] == 0:
            return True
        else:
            return False
    elif x == None or x == []:
        return False
    else:
        raise Exception("is_column expects one of the following types: np.ndarray, casadi.MX, casadi.SX."
                        + " Got: " + str(type(x)))