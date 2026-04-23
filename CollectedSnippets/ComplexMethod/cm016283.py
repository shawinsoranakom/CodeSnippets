def generate_code(
    gen_dir: Path,
    native_functions_path: str | None = None,
    tags_path: str | None = None,
    install_dir: str | None = None,
    subset: str | None = None,
    disable_autograd: bool = False,
    force_schema_registration: bool = False,
    operator_selector: Any = None,
) -> None:
    from tools.autograd.gen_annotated_fn_args import gen_annotated
    from tools.autograd.gen_autograd import gen_autograd, gen_autograd_python

    from torchgen.selective_build.selector import SelectiveBuilder

    # Build ATen based Variable classes
    if install_dir is None:
        install_dir = os.fspath(gen_dir / "torch/csrc")
        python_install_dir = os.fspath(gen_dir / "torch/testing/_internal/generated")
    else:
        python_install_dir = install_dir
    autograd_gen_dir = os.path.join(install_dir, "autograd", "generated")
    for d in (autograd_gen_dir, python_install_dir):
        os.makedirs(d, exist_ok=True)
    autograd_dir = os.fspath(Path(__file__).parent.parent / "autograd")

    if subset == "pybindings" or not subset:
        gen_autograd_python(
            native_functions_path or NATIVE_FUNCTIONS_PATH,
            tags_path or TAGS_PATH,
            autograd_gen_dir,
            autograd_dir,
        )

    if operator_selector is None:
        operator_selector = SelectiveBuilder.get_nop_selector()

    if subset == "libtorch" or not subset:
        gen_autograd(
            native_functions_path or NATIVE_FUNCTIONS_PATH,
            tags_path or TAGS_PATH,
            autograd_gen_dir,
            autograd_dir,
            disable_autograd=disable_autograd,
            operator_selector=operator_selector,
        )

    if subset == "python" or not subset:
        gen_annotated(
            native_functions_path or NATIVE_FUNCTIONS_PATH,
            tags_path or TAGS_PATH,
            python_install_dir,
            autograd_dir,
        )