def create_tmp_repo(tmp_dir, models=None):
    """
    Creates a repository in a temporary directory mimicking the structure of Transformers. Uses the list of models
    provided (which defaults to just `["bert"]`).
    """
    tmp_dir = Path(tmp_dir)
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(exist_ok=True)
    repo = Repo.init(tmp_dir)

    if models is None:
        models = ["bert"]
    class_names = [model[0].upper() + model[1:] for model in models]

    transformers_dir = tmp_dir / "src" / "transformers"
    transformers_dir.mkdir(parents=True, exist_ok=True)
    with open(transformers_dir / "__init__.py", "w") as f:
        init_lines = ["from .utils import cached_file, is_torch_available"]
        init_lines.extend(
            [f"from .models.{model} import {cls}Config, {cls}Model" for model, cls in zip(models, class_names)]
        )
        f.write("\n".join(init_lines) + "\n")
    with open(transformers_dir / "configuration_utils.py", "w") as f:
        f.write("from .utils import cached_file\n\ncode")
    with open(transformers_dir / "modeling_utils.py", "w") as f:
        f.write("from .utils import cached_file\n\ncode")

    utils_dir = tmp_dir / "src" / "transformers" / "utils"
    utils_dir.mkdir(exist_ok=True)
    with open(utils_dir / "__init__.py", "w") as f:
        f.write("from .hub import cached_file\nfrom .imports import is_torch_available\n")
    with open(utils_dir / "hub.py", "w") as f:
        f.write("import huggingface_hub\n\ncode")
    with open(utils_dir / "imports.py", "w") as f:
        f.write("code")

    model_dir = tmp_dir / "src" / "transformers" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    with open(model_dir / "__init__.py", "w") as f:
        f.write("\n".join([f"import {model}" for model in models]))

    for model, cls in zip(models, class_names):
        model_dir = tmp_dir / "src" / "transformers" / "models" / model
        model_dir.mkdir(parents=True, exist_ok=True)
        with open(model_dir / "__init__.py", "w") as f:
            f.write(f"from .configuration_{model} import {cls}Config\nfrom .modeling_{model} import {cls}Model\n")
        with open(model_dir / f"configuration_{model}.py", "w") as f:
            f.write("from ...configuration_utils import PreTrainedConfig\ncode")
        with open(model_dir / f"modeling_{model}.py", "w") as f:
            modeling_code = BERT_MODEL_FILE.replace("bert", model).replace("Bert", cls)
            f.write(modeling_code)

    test_dir = tmp_dir / "tests"
    test_dir.mkdir(exist_ok=True)
    with open(test_dir / "test_modeling_common.py", "w") as f:
        f.write("from transformers.modeling_utils import PreTrainedModel\ncode")

    for model, cls in zip(models, class_names):
        test_model_dir = test_dir / "models" / model
        test_model_dir.mkdir(parents=True, exist_ok=True)
        (test_model_dir / "__init__.py").touch()
        with open(test_model_dir / f"test_modeling_{model}.py", "w") as f:
            f.write(
                f"from transformers import {cls}Config, {cls}Model\nfrom ...test_modeling_common import ModelTesterMixin\n\ncode"
            )

    example_dir = tmp_dir / "examples"
    example_dir.mkdir(exist_ok=True)
    framework_dir = example_dir / "pytorch"
    framework_dir.mkdir(exist_ok=True)
    with open(framework_dir / "test_pytorch_examples.py", "w") as f:
        f.write("""test_args = "run_glue.py"\n""")
    glue_dir = framework_dir / "text-classification"
    glue_dir.mkdir(exist_ok=True)
    with open(glue_dir / "run_glue.py", "w") as f:
        f.write("from transformers import BertModel\n\ncode")

    repo.index.add(["examples", "src", "tests"])
    repo.index.commit("Initial commit")
    if "main" not in repo.heads:
        repo.create_head("main")
    repo.head.reference = repo.refs.main
    if "master" in repo.heads:
        repo.delete_head("master")
    return repo