def sparseness(x):
    if isinstance(x, KerasTensor):
        return "sparse" if x.sparse else "dense"
    elif x.__class__.__name__ == "BCOO":
        if x.n_dense > 0:
            return "slices"
        else:
            return "sparse"
    elif x.__class__.__name__ == "SparseTensor":
        return "sparse"
    elif x.__class__.__name__ == "IndexedSlices":
        return "slices"
    elif not hasattr(x, "shape") or not x.shape:
        return "scalar"
    else:
        return "dense"