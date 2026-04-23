def run_doctests(test_module, test_directory, options):
    """
    Assumes the incoming test module is called doctest, and simply executes the
    xdoctest runner on the torch library itself.
    """
    import xdoctest

    pkgpath = Path(torch.__file__).parent

    exclude_module_list = ["torch._vendor.*"]
    enabled = {
        # TODO: expose these options to the user
        # For now disable all feature-conditional tests
        # 'lapack': 'auto',
        # 'cuda': 'auto',
        # 'cuda1': 'auto',
        # 'qengine': 'auto',
        "lapack": 0,
        "cuda": 0,
        "cuda1": 0,
        "qengine": 0,
        "autograd_profiler": 0,
        "cpp_ext": 0,
        "monitor": 0,
        "onnx": "auto",
    }

    # Resolve "auto" based on a test to determine if the feature is available.
    if enabled["cuda"] == "auto" and torch.cuda.is_available():
        enabled["cuda"] = True

    if (
        enabled["cuda1"] == "auto"
        and torch.cuda.is_available()
        and torch.cuda.device_count() > 1
    ):
        enabled["cuda1"] = True

    if enabled["lapack"] == "auto" and torch._C.has_lapack:
        enabled["lapack"] = True

    if enabled["qengine"] == "auto":
        try:
            # Is there a better check if quantization is enabled?
            import torch.ao.nn.quantized as nnq  # NOQA: F401

            torch.backends.quantized.engine = "qnnpack"
            torch.backends.quantized.engine = "fbgemm"
        except (ImportError, RuntimeError):
            ...
        else:
            enabled["qengine"] = True

    if enabled["onnx"] == "auto":
        try:
            import onnx  # NOQA: F401
            import onnxruntime  # NOQA: F401
            import onnxscript  # NOQA: F401
        except ImportError:
            exclude_module_list.append("torch.onnx.*")
            enabled["onnx"] = False
        else:
            enabled["onnx"] = True

    # Set doctest environment variables
    if enabled["cuda"]:
        os.environ["TORCH_DOCTEST_CUDA"] = "1"

    if enabled["cuda1"]:
        os.environ["TORCH_DOCTEST_CUDA1"] = "1"

    if enabled["lapack"]:
        os.environ["TORCH_DOCTEST_LAPACK"] = "1"

    if enabled["qengine"]:
        os.environ["TORCH_DOCTEST_QENGINE"] = "1"

    if enabled["autograd_profiler"]:
        os.environ["TORCH_DOCTEST_AUTOGRAD_PROFILER"] = "1"

    if enabled["cpp_ext"]:
        os.environ["TORCH_DOCTEST_CPP_EXT"] = "1"

    if enabled["monitor"]:
        os.environ["TORCH_DOCTEST_MONITOR"] = "1"

    if enabled["onnx"]:
        os.environ["TORCH_DOCTEST_ONNX"] = "1"

    if torch.mps.is_available():
        os.environ["TORCH_DOCTEST_MPS"] = "1"

    if torch.distributed.is_available():
        os.environ["TORCH_DOCTEST_DISTRIBUTED"] = "1"

    if 0:
        # TODO: could try to enable some of these
        os.environ["TORCH_DOCTEST_QUANTIZED_DYNAMIC"] = "1"
        os.environ["TORCH_DOCTEST_ANOMALY"] = "1"
        os.environ["TORCH_DOCTEST_AUTOGRAD"] = "1"
        os.environ["TORCH_DOCTEST_HUB"] = "1"
        os.environ["TORCH_DOCTEST_DATALOADER"] = "1"
        os.environ["TORCH_DOCTEST_FUTURES"] = "1"

    pkgpath = os.path.dirname(torch.__file__)

    xdoctest_config = {
        "global_exec": r"\n".join(
            [
                "from torch import nn",
                "import torch.nn.functional as F",
                "import torch",
            ]
        ),
        "analysis": "static",  # set to "auto" to test doctests in compiled modules
        "style": "google",
        "options": "+IGNORE_WHITESPACE",
    }
    xdoctest_verbose = max(1, options.verbose)
    run_summary = xdoctest.runner.doctest_module(
        os.fspath(pkgpath),
        config=xdoctest_config,
        verbose=xdoctest_verbose,
        command=options.xdoctest_command,
        argv=[],
        exclude=exclude_module_list,
    )
    result = 1 if run_summary.get("n_failed", 0) else 0
    return result