async def get_best_of_n_evals(request: Request):
    # Get all query parameters
    query_params = dict(request.query_params)

    # Extract all folder paths (folder1, folder2, folder3, etc.)
    folders: list[str] = []
    i = 1
    while f"folder{i}" in query_params:
        folders.append(query_params[f"folder{i}"])
        i += 1

    if not folders:
        return {"error": "No folders provided"}

    # Validate folders exist
    for folder in folders:
        if not os.path.exists(folder):
            return {"error": f"Folder does not exist: {folder}"}

    evals: list[Eval] = []
    folder_names = [os.path.basename(folder) for folder in folders]

    # Get HTML files from all folders
    files_by_folder = []
    for folder in folders:
        files = {
            f: os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.endswith(".html")
        }
        files_by_folder.append(files)

    # Find common base names across all folders
    common_names: Set[str] = set()
    base_names_first_folder = {
        f.rsplit("_", 1)[0] if "_" in f else f.replace(".html", "")
        for f in files_by_folder[0].keys()
    }

    for base_name in base_names_first_folder:
        found_in_all = True
        for folder_files in files_by_folder[1:]:
            if not any(f.startswith(base_name) for f in folder_files.keys()):
                found_in_all = False
                break
        if found_in_all:
            common_names.add(base_name)

    # For each matching set, create an eval
    for base_name in common_names:
        # Find the corresponding input image
        input_image = None
        input_path = os.path.join(EVALS_DIR, "inputs", f"{base_name}.png")
        if os.path.exists(input_path):
            input_image = await image_to_data_url(input_path)
        else:
            input_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

        # Get HTML contents from all folders
        outputs: list[str] = []
        for folder_files in files_by_folder:
            output_content: str | None = None
            for filename in folder_files.keys():
                if filename.startswith(base_name):
                    with open(folder_files[filename], "r") as f:
                        output_content = f.read()
                    break
            if output_content:
                outputs.append(output_content)
            else:
                outputs.append("<html><body>Output not found</body></html>")

        if len(outputs) == len(folders):  # Only add if we have outputs from all folders
            evals.append(Eval(input=input_image, outputs=outputs))

    return BestOfNEvalsResponse(evals=evals, folder_names=folder_names)