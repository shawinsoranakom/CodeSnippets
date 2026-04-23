def destroy_model_parallel():
    """Set the groups to none and destroy them."""
    global _TP

    if _TP:
        _TP.destroy()
    _TP = None

    global _DCP
    if _DCP:
        _DCP.destroy()
    _DCP = None

    global _PCP
    if _PCP:
        _PCP.destroy()
    _PCP = None

    global _PP
    if _PP:
        _PP.destroy()
    _PP = None

    global _DP
    if _DP:
        _DP.destroy()
    _DP = None

    global _EP
    if _EP:
        _EP.destroy()
    _EP = None

    global _EPLB
    if _EPLB:
        _EPLB.destroy()
    _EPLB = None