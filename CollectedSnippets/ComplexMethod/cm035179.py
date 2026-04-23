def check_device(
    use_gpu,
    use_xpu=False,
    use_npu=False,
    use_mlu=False,
    use_gcu=False,
    use_iluvatar_gpu=False,
    use_metax_gpu=False,
):
    """
    Log error and exit when set use_gpu=true in paddlepaddle
    cpu version.
    """
    err = (
        "Config {} cannot be set as true while your paddle "
        "is not compiled with {} ! \nPlease try: \n"
        "\t1. Install paddlepaddle to run model on {} \n"
        "\t2. Set {} as false in config file to run "
        "model on CPU"
    )

    try:
        if use_gpu and use_xpu:
            print("use_xpu and use_gpu can not both be true.")
        if use_gpu and not paddle.is_compiled_with_cuda():
            print(err.format("use_gpu", "cuda", "gpu", "use_gpu"))
            sys.exit(1)
        if use_xpu and not paddle.device.is_compiled_with_xpu():
            print(err.format("use_xpu", "xpu", "xpu", "use_xpu"))
            sys.exit(1)
        if use_npu:
            if (
                int(paddle.version.major) != 0
                and int(paddle.version.major) <= 2
                and int(paddle.version.minor) <= 4
            ):
                if not paddle.device.is_compiled_with_npu():
                    print(err.format("use_npu", "npu", "npu", "use_npu"))
                    sys.exit(1)
            # is_compiled_with_npu() has been updated after paddle-2.4
            else:
                if not paddle.device.is_compiled_with_custom_device("npu"):
                    print(err.format("use_npu", "npu", "npu", "use_npu"))
                    sys.exit(1)
        if use_mlu and not paddle.device.is_compiled_with_mlu():
            print(err.format("use_mlu", "mlu", "mlu", "use_mlu"))
            sys.exit(1)
        if use_gcu and not paddle.device.is_compiled_with_custom_device("gcu"):
            print(err.format("use_gcu", "gcu", "gcu", "use_gcu"))
            sys.exit(1)
        if use_metax_gpu and not paddle.device.is_compiled_with_custom_device(
            "metax_gpu"
        ):
            print(
                err.format("use_metax_gpu", "metax_gpu", "metax_gpu", "use_metax_gpu")
            )
            sys.exit(1)

    except Exception as e:
        pass