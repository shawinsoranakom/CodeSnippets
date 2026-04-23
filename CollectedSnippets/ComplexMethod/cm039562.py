def _check_output(out_np, out_xp, xp_to, y2_xp):
    if isinstance(out_np, float):
        assert isinstance(out_xp, float)
    elif hasattr(out_np, "shape"):
        assert hasattr(out_xp, "shape")
        assert get_namespace(out_xp)[0] == xp_to
        assert array_api_device(out_xp) == array_api_device(y2_xp)
    # `classification_report` returns str (with default `output_dict=False`)
    elif isinstance(out_np, str):
        assert isinstance(out_xp, str)