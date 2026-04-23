async def get_evals(folder: str):
    if not folder:
        raise HTTPException(status_code=400, detail="Folder path is required")

    folder_path = Path(folder)
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder}")

    try:
        evals: list[Eval] = []
        # Get all HTML files from folder
        files = {
            f: os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.endswith(".html")
        }

        # Extract base names
        base_names: Set[str] = set()
        for filename in files.keys():
            base_name = (
                filename.rsplit("_", 1)[0]
                if "_" in filename
                else filename.replace(".html", "")
            )
            base_names.add(base_name)

        for base_name in base_names:
            input_path = os.path.join(EVALS_DIR, "inputs", f"{base_name}.png")
            if not os.path.exists(input_path):
                continue

            # Find matching output file
            output_file = None
            for filename, filepath in files.items():
                if filename.startswith(base_name):
                    output_file = filepath
                    break

            if output_file:
                input_data = await image_to_data_url(input_path)
                with open(output_file, "r", encoding="utf-8") as f:
                    output_html = f.read()
                evals.append(Eval(input=input_data, outputs=[output_html]))

        return evals

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing evals: {str(e)}")