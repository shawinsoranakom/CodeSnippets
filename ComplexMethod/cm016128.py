def check_accuracy(actual_csv, expected_csv, expected_filename):
    failed = []
    improved = []

    if "rocm" in expected_filename:
        flaky_models.update(
            {
                "Background_Matting",
                "mnasnet1_0",
                "llava",
                "repvgg_a2",
                "resnet152",
                "resnet18",
                "resnet50",
                "stable_diffusion_unet",
                "torchrec_dlrm",
                "shufflenet_v2_x1_0",
                "vgg16",
                "BERT_pytorch",
                # LLM
                "google/gemma-2-2b",
                "tts_angular",  # RuntimeError: Cannot access data pointer of Tensor
                # Discovered on gfx950 CI after ROCm 7.2 upgrade, eager mode non determinism
                "alexnet",
                "demucs",
            }
        )

    for model in actual_csv["name"]:
        accuracy = get_field(actual_csv, model, "accuracy")
        expected_accuracy = get_field(expected_csv, model, "accuracy")

        if accuracy is None:
            status = "MISSING_ACCURACY:"
            failed.append(model)
        elif expected_accuracy is None:
            status = "MISSING_EXPECTED:"
            failed.append(model)
        elif accuracy == expected_accuracy:
            status = "PASS" if expected_accuracy == "pass" else "XFAIL"
            print(f"{model:34}  {status}")
            continue
        elif model in flaky_models:
            if accuracy == "pass":
                # model passed but marked xfailed
                status = "PASS_BUT_FLAKY:"
            else:
                # model failed but marked passe
                status = "FAIL_BUT_FLAKY:"
        elif accuracy != "pass":
            status = "FAIL:"
            failed.append(model)
        else:
            status = "IMPROVED:"
            improved.append(model)
        print(
            f"{model:34}  {status:9} accuracy={accuracy}, expected={expected_accuracy}"
        )

    msg = ""
    if failed or improved:
        if failed:
            msg += textwrap.dedent(
                f"""
            Error: {len(failed)} models have accuracy status regressed:
                {" ".join(failed)}

            """
            )
        if improved:
            msg += textwrap.dedent(
                f"""
            Improvement: {len(improved)} models have accuracy status improved:
                {" ".join(improved)}

            """
            )
        sha = os.getenv("SHA1", "{your CI commit sha}")
        msg += textwrap.dedent(
            f"""
        If this change is expected, you can update `{expected_filename}` to reflect the new baseline.
        from pytorch/pytorch root, run
        `python benchmarks/dynamo/ci_expected_accuracy/update_expected.py {sha}`
        and then `git add` the resulting local changes to expected CSVs to your commit.
        """
        )
    return failed or improved, msg