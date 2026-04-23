def run_tests(needs: str | tuple[str, ...] = ()) -> None:
    from torch.testing._internal.common_utils import run_tests

    if TEST_WITH_TORCHDYNAMO or TEST_WITH_CROSSREF:
        return  # skip testing

    if (
        not torch.xpu.is_available()
        and IS_WINDOWS
        and os.environ.get("TORCHINDUCTOR_WINDOWS_TESTS", "0") == "0"
    ):
        return

    if isinstance(needs, str):
        needs = (needs,)
    for need in needs:
        if need == "cuda":
            if not torch.cuda.is_available():
                return
        else:
            try:
                importlib.import_module(need)
            except ImportError:
                return

    run_tests()