async def get_pairwise_evals(
    folder1: str = Query(
        "...",
        description="Absolute path to first folder",
    ),
    folder2: str = Query(
        "..",
        description="Absolute path to second folder",
    ),
):
    if not os.path.exists(folder1) or not os.path.exists(folder2):
        return {"error": "One or both folders do not exist"}

    evals: list[Eval] = []

    # Get all HTML files from first folder
    files1 = {
        f: os.path.join(folder1, f) for f in os.listdir(folder1) if f.endswith(".html")
    }
    files2 = {
        f: os.path.join(folder2, f) for f in os.listdir(folder2) if f.endswith(".html")
    }

    # Find common base names (ignoring any suffixes)
    common_names: Set[str] = set()
    for f1 in files1.keys():
        base_name: str = f1.rsplit("_", 1)[0] if "_" in f1 else f1.replace(".html", "")
        for f2 in files2.keys():
            if f2.startswith(base_name):
                common_names.add(base_name)

    # For each matching pair, create an eval
    for base_name in common_names:
        # Find the corresponding input image
        input_image = None
        input_path = os.path.join(EVALS_DIR, "inputs", f"{base_name}.png")
        if os.path.exists(input_path):
            input_image = await image_to_data_url(input_path)
        else:
            input_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="  # 1x1 transparent PNG

        # Get the HTML contents
        output1 = None
        output2 = None

        # Find matching files in folder1
        for f1 in files1.keys():
            if f1.startswith(base_name):
                with open(files1[f1], "r") as f:
                    output1 = f.read()
                break

        # Find matching files in folder2
        for f2 in files2.keys():
            if f2.startswith(base_name):
                with open(files2[f2], "r") as f:
                    output2 = f.read()
                break

        if output1 and output2:
            evals.append(Eval(input=input_image, outputs=[output1, output2]))

    # Extract folder names for the UI
    folder1_name = os.path.basename(folder1)
    folder2_name = os.path.basename(folder2)

    return PairwiseEvalResponse(
        evals=evals, folder1_name=folder1_name, folder2_name=folder2_name
    )