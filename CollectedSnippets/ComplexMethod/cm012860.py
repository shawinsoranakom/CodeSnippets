def get_default_qconfig(backend="x86", version=0):
    """
    Returns the default PTQ qconfig for the specified backend.

    Args:
      * `backend` (str): a string representing the target backend. Currently supports
        `x86` (default), `fbgemm`, `qnnpack` and `onednn`.

    Return:
        qconfig
    """
    supported_backends = ["fbgemm", "x86", "qnnpack", "onednn"]
    if backend not in supported_backends:
        raise AssertionError(
            "backend: "
            + str(backend)
            + f" not supported. backend must be one of {supported_backends}"
        )

    if version == 0:
        if backend == "fbgemm":
            qconfig = QConfig(
                activation=HistogramObserver.with_args(reduce_range=True),
                weight=default_per_channel_weight_observer,
            )
        elif backend == "qnnpack":
            # TODO: make this compatible with xnnpack constraints
            qconfig = QConfig(
                activation=HistogramObserver.with_args(reduce_range=False),
                weight=default_weight_observer,
            )
        elif backend == "onednn":
            if not torch.cpu._is_vnni_supported():
                warnings.warn(
                    "Default qconfig of oneDNN backend with reduce_range of false may have accuracy issues "
                    "on CPU without Vector Neural Network Instruction support.",
                    stacklevel=2,
                )
            qconfig = QConfig(
                activation=HistogramObserver.with_args(reduce_range=False),
                weight=default_per_channel_weight_observer,
            )
        elif backend == "x86":
            qconfig = QConfig(
                activation=HistogramObserver.with_args(reduce_range=True),
                weight=default_per_channel_weight_observer,
            )
        else:
            # won't reach
            qconfig = default_qconfig
    else:
        raise AssertionError(
            "Version number: "
            + str(version)
            + " in get_default_qconfig is not supported. Version number must be 0"
        )

    return qconfig