def highlight_max(s, props=""):
    return np.where(s == np.nanmax(s.values), props, "")