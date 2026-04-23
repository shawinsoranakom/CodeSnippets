def test_infer_tests_to_run(self):
        with tempfile.TemporaryDirectory() as tmp_folder:
            tmp_folder = Path(tmp_folder)
            models = ["bert", "gpt2"] + [f"bert{i}" for i in range(10)]
            repo = create_tmp_repo(tmp_folder, models=models)

            commit_changes("src/transformers/models/bert/modeling_bert.py", BERT_MODEL_FILE_NEW_CODE, repo)

            example_tests = {
                "examples/pytorch/test_pytorch_examples.py",
            }

            with patch_transformer_repo_path(tmp_folder):
                infer_tests_to_run(tmp_folder / "test-output.txt", diff_with_last_commit=True)
                with open(tmp_folder / "test-output.txt") as f:
                    tests_to_run = f.read()
                with open(tmp_folder / "examples_test_list.txt") as f:
                    example_tests_to_run = f.read()

            assert tests_to_run == "tests/models/bert/test_modeling_bert.py"
            assert set(example_tests_to_run.split(" ")) == example_tests

            # Fake a new model addition
            repo = create_tmp_repo(tmp_folder, models=models)

            branch = repo.create_head("new_model")
            branch.checkout()

            with open(tmp_folder / "src/transformers/__init__.py", "a") as f:
                f.write("from .models.t5 import T5Config, T5Model\n")

            model_dir = tmp_folder / "src/transformers/models/t5"
            model_dir.mkdir(exist_ok=True)

            with open(model_dir / "__init__.py", "w") as f:
                f.write("from .configuration_t5 import T5Config\nfrom .modeling_t5 import T5Model\n")
            with open(model_dir / "configuration_t5.py", "w") as f:
                f.write("from ...configuration_utils import PreTrainedConfig\ncode")
            with open(model_dir / "modeling_t5.py", "w") as f:
                modeling_code = BERT_MODEL_FILE.replace("bert", "t5").replace("Bert", "T5")
                f.write(modeling_code)

            test_dir = tmp_folder / "tests/models/t5"
            test_dir.mkdir(exist_ok=True)
            (test_dir / "__init__.py").touch()
            with open(test_dir / "test_modeling_t5.py", "w") as f:
                f.write(
                    "from transformers import T5Config, T5Model\nfrom ...test_modeling_common import ModelTesterMixin\n\ncode"
                )

            repo.index.add(["src", "tests"])
            repo.index.commit("Add T5 model")

            with patch_transformer_repo_path(tmp_folder):
                infer_tests_to_run(tmp_folder / "test-output.txt")
                with open(tmp_folder / "test-output.txt") as f:
                    tests_to_run = f.read()
                with open(tmp_folder / "examples_test_list.txt") as f:
                    example_tests_to_run = f.read()

            expected_tests = {
                "tests/models/bert/test_modeling_bert.py",
                "tests/models/gpt2/test_modeling_gpt2.py",
                "tests/models/t5/test_modeling_t5.py",
                "tests/test_modeling_common.py",
            }
            assert set(tests_to_run.split(" ")) == expected_tests
            assert set(example_tests_to_run.split(" ")) == example_tests

            with patch_transformer_repo_path(tmp_folder):
                infer_tests_to_run(tmp_folder / "test-output.txt")
                with open(tmp_folder / "test-output.txt") as f:
                    tests_to_run = f.read()
                with open(tmp_folder / "examples_test_list.txt") as f:
                    example_tests_to_run = f.read()

            expected_tests = [f"tests/models/{name}/test_modeling_{name}.py" for name in models + ["t5"]]
            expected_tests = set(expected_tests + ["tests/test_modeling_common.py"])
            assert set(tests_to_run.split(" ")) == expected_tests
            assert set(example_tests_to_run.split(" ")) == example_tests