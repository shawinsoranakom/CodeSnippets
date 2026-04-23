def _update_out(out, out_name, out_value, auxiliary=True, update_aux=True):
    """Helper function to update output dictionary with main and auxiliary outputs."""
    out[out_name] = out_value[-1] if auxiliary else out_value
    if auxiliary and update_aux:
        if "aux_outputs" not in out:
            out["aux_outputs"] = [{} for _ in range(len(out_value) - 1)]
        assert len(out["aux_outputs"]) == len(out_value) - 1
        for aux_output, aux_value in zip(out["aux_outputs"], out_value[:-1]):
            aux_output[out_name] = aux_value