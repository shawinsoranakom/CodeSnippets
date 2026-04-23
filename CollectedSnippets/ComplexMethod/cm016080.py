def main(output_file=DEFAULT_OUTPUT_FILE, only_model=None):
    results = []

    if not only_model:
        experiments = all_experiments.values()
    else:
        if only_model not in all_experiments:
            print(
                f"Unknown model: {only_model}, all available models: {all_experiments.keys()}"
            )
        # only run the specified model
        experiments = [all_experiments[only_model]]
    for func in experiments:
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except AssertionError:
            # This happens when torch is compiled with CUDA turning off completely
            device = "cpu"

        torch.compiler.cudagraph_mark_step_begin()
        lst = func(device)
        for x in lst:
            results.append(dataclasses.astuple(x))

    headers = [field.name for field in dataclasses.fields(Experiment)]

    for row in results:
        output_csv(output_file, headers, row)
        # Also write the output in JSON format so that it can be ingested into the OSS benchmark database
        output_json(output_file, headers, row)