def _compute_n_patches(i_h, i_w, p_h, p_w, max_patches=None):
    """Compute the number of patches that will be extracted in an image.

    Read more in the :ref:`User Guide <image_feature_extraction>`.

    Parameters
    ----------
    i_h : int
        The image height
    i_w : int
        The image with
    p_h : int
        The height of a patch
    p_w : int
        The width of a patch
    max_patches : int or float, default=None
        The maximum number of patches to extract. If `max_patches` is a float
        between 0 and 1, it is taken to be a proportion of the total number
        of patches. If `max_patches` is None, all possible patches are extracted.
    """
    n_h = i_h - p_h + 1
    n_w = i_w - p_w + 1
    all_patches = n_h * n_w

    if max_patches:
        if isinstance(max_patches, (Integral)) and max_patches < all_patches:
            return max_patches
        elif isinstance(max_patches, (Integral)) and max_patches >= all_patches:
            return all_patches
        elif isinstance(max_patches, (Real)) and 0 < max_patches < 1:
            return int(max_patches * all_patches)
        else:
            raise ValueError("Invalid value for max_patches: %r" % max_patches)
    else:
        return all_patches