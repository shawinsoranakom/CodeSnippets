def models_list(*, all: bool = True, keywords: list[str] | None = None):
    TEST_MODELS: list[tuple[str, dict[str, Any]]] = [
        ("facebook/opt-125m", {}),
        (
            "neuralmagic/Llama-3.2-1B-Instruct-FP8-dynamic",
            {"dtype": torch.float16},
        ),
        ("meta-llama/Llama-3.2-1B-Instruct", {}),
    ]

    if all:
        TEST_MODELS.extend(
            [
                ("neuralmagic/Llama-3.2-1B-Instruct-quantized.w8a8", {}),
                (
                    "nm-testing/tinyllama-oneshot-w8w8-test-static-shape-change",
                    {"dtype": torch.float16},
                ),
            ]
        )

        # TODO: figure out why this fails.
        if False and is_quant_method_supported("gguf"):  # noqa: SIM223
            TEST_MODELS.append(
                ("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF", {"quantization": "gguf"})
            )

        if is_quant_method_supported("gptq"):
            TEST_MODELS.append(
                ("TheBloke/TinyLlama-1.1B-Chat-v0.3-GPTQ", {"quantization": "gptq"})
            )

        if is_quant_method_supported("gptq_marlin"):
            TEST_MODELS.append(
                (
                    "TheBloke/TinyLlama-1.1B-Chat-v1.0-GPTQ",
                    {"quantization": "gptq_marlin"},
                )
            )

        if not current_platform.is_rocm() and is_quant_method_supported("awq"):
            TEST_MODELS.append(
                ("TheBloke/TinyLlama-1.1B-Chat-v0.3-AWQ", {"quantization": "AWQ"})
            )

    if keywords is None:
        return TEST_MODELS

    # filter by keywords
    pred = lambda model: any(keyword in model[0] for keyword in keywords)
    return list(filter(pred, TEST_MODELS))