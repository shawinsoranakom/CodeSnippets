def categorize(features):
        title = features["title"]
        labels = features["labels"]
        category = "Uncategorized"
        topic = "Untopiced"

        # Revert commits are merged directly to master with no associated PR number
        if features["pr_number"] is None:
            if title.startswith("Revert"):
                return "skip", topic

        # We ask contributors to label their PR's appropriately
        # when they're first landed.
        # Check if the labels are there first.
        already_categorized = already_topiced = False
        for label in labels:
            if label.startswith("release notes: "):
                category = label.split("release notes: ", 1)[1]
                category = CommitList.category_remapper(category)
                already_categorized = True
            if label.startswith("topic: "):
                topic = label.split("topic: ", 1)[1]
                already_topiced = True
        if already_categorized and already_topiced:
            return category, topic

        # update this to check if each file starts with caffe2
        if "caffe2" in title:
            return "caffe2", topic
        if "Reverted" in labels:
            return "skip", topic
        if "module: deprecation" in labels:
            topic = "deprecation"

        found_bracket_category = CommitList.bracket_category_matcher(title)
        if found_bracket_category:
            return found_bracket_category, topic

        files_changed = features["files_changed"]
        for file in files_changed:
            file_lowercase = file.lower()
            if CommitList.keywordInFile(
                file,
                [
                    "docker/",
                    ".github",
                    ".jenkins",
                    ".ci",
                    ".azure_pipelines",
                ],
            ):
                category = "releng"
                break
            # datapipe(s), torch/utils/data, test_{dataloader, datapipe}
            if CommitList.keywordInFile(
                file, ["torch/utils/data", "test_dataloader", "test_datapipe"]
            ):
                category = "dataloader_frontend"
                break
            if CommitList.keywordInFile(file, ["torch/csrc/api", "test/cpp/api"]):
                category = "cpp_frontend"
                break
            if CommitList.keywordInFile(file, ["distributed", "c10d"]):
                category = "distributed"
                break
            if "vulkan" in file_lowercase:
                category = "vulkan"
                break
            if "Foreach" in file_lowercase:
                category = "foreach_frontend"
                break
            if "onnx" in file_lowercase:
                category = "onnx"
                break
            if CommitList.keywordInFile(file, ["torch/fx", "test_fx"]):
                category = "fx"
                break
            if CommitList.keywordInFile(file, ["torch/ao", "test/ao"]):
                category = common.quantization.name
                break
            # torch/quantization, test/quantization, aten/src/ATen/native/quantized, torch/nn/{quantized, quantizable}
            if CommitList.keywordInFile(
                file,
                [
                    "torch/quantization",
                    "test/quantization",
                    "aten/src/ATen/native/quantized",
                    "torch/nn/quantiz",
                ],
            ):
                category = common.quantization.name
                break
            if CommitList.keywordInFile(file, ["torch/package", "test/package"]):
                category = "package"
                break
            if CommitList.keywordInFile(
                file,
                [
                    "torch/csrc/jit/mobile",
                    "aten/src/ATen/native/metal",
                    "test/mobile",
                    "torch/backends/_nnapi/",
                    "test/test_nnapi.py",
                ],
            ):
                category = "mobile"
                break
            if CommitList.keywordInFile(
                file,
                [
                    "aten/src/ATen/native/LinearAlgebra.cpp",
                    "test/test_linalg.py",
                    "torch/linalg",
                ],
            ):
                category = "linalg_frontend"
                break
            if CommitList.keywordInFile(
                file,
                [
                    "torch/sparse",
                    "aten/src/ATen/native/sparse",
                    "torch/_masked/__init__.py",
                ],
            ):
                category = "sparse_frontend"
                break
            if CommitList.keywordInFile(file, ["tools/autograd"]):
                category = "autograd_frontend"
                break
            if CommitList.keywordInFile(
                file,
                [
                    "test/test_nn.py",
                    "test/test_module.py",
                    "torch/nn/modules",
                    "torch/nn/functional.py",
                ],
            ):
                category = "nn_frontend"
                break
            if CommitList.keywordInFile(file, ["torch/csrc/jit", "torch/jit"]):
                category = "jit"
                break
            if CommitList.keywordInFile(
                file,
                [
                    "torch/_meta_registrations.py",
                    "torch/_decomp",
                    "torch/_prims",
                    "torch/_refs",
                ],
            ):
                category = "composability"
                break
            if CommitList.keywordInFile(file, ["torch/_dynamo"]):
                category = "dynamo"
                break
            if CommitList.keywordInFile(file, ["torch/_inductor"]):
                category = "inductor"
                break
        else:
            # Below are some extra quick checks that aren't necessarily file-path related,
            # but I found that to catch a decent number of extra commits.
            if len(files_changed) > 0 and all(
                f_name.endswith((".cu", ".cuh")) for f_name in files_changed
            ):
                category = "cuda"
            elif "[PyTorch Edge]" in title:
                category = "mobile"
            elif (
                len(files_changed) == 1
                and "torch/testing/_internal/common_methods_invocations.py"
                in files_changed[0]
            ):
                # when this is the only file changed, it's almost always an OpInfo change.
                category = "python_frontend"
            elif len(files_changed) == 1 and "torch/_torch_docs.py" in files_changed[0]:
                # individual torch_docs changes are usually for python ops
                category = "python_frontend"

        # If we couldn't find a category but the topic is not user facing we can skip these:
        if category == "Uncategorized" and topic == "not user facing":
            category = "skip"

        return category, topic