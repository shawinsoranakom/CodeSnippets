def download_and_combine_aime_datasets(data_dir: str = "./data/aime") -> str:
    """Download all AIME datasets and combine them into a single file"""

    datasets = {
        "test2024": "https://raw.githubusercontent.com/GAIR-NLP/AIME-Preview/main/eval/data/aime/test2024.jsonl",
        "test2025-I": "https://raw.githubusercontent.com/GAIR-NLP/AIME-Preview/main/eval/data/aime/test2025-I.jsonl",
        "test2025-II": "https://raw.githubusercontent.com/GAIR-NLP/AIME-Preview/main/eval/data/aime/test2025-II.jsonl",
    }

    os.makedirs(data_dir, exist_ok = True)
    combined_filepath = os.path.join(data_dir, "aime.jsonl")

    # Check if combined file already exists
    if os.path.exists(combined_filepath):
        print(f"Combined AIME dataset already exists at {combined_filepath}")
        return combined_filepath

    print("Downloading and combining AIME datasets...")

    all_problems = []
    global_id = 0

    for dataset_name, url in datasets.items():
        print(f"  Downloading {dataset_name}...")

        try:
            response = requests.get(url)
            response.raise_for_status()

            # Parse each line and add source information
            for line_num, line in enumerate(response.text.strip().split("\n")):
                if line.strip():
                    try:
                        data = json.loads(line)
                        # Add source dataset information and global ID
                        data["source_dataset"] = dataset_name
                        data["original_id"] = data.get("id", line_num)
                        data["global_id"] = global_id
                        global_id += 1
                        all_problems.append(data)
                    except json.JSONDecodeError as e:
                        print(
                            f"    Warning: Error parsing line {line_num + 1} in {dataset_name}: {e}"
                        )
                        continue

        except requests.RequestException as e:
            print(f"    Error downloading {dataset_name}: {e}")
            continue

    # Write combined dataset
    if all_problems:
        with open(combined_filepath, "w", encoding = "utf-8") as f:
            for problem in all_problems:
                f.write(json.dumps(problem, ensure_ascii = False) + "\n")

        print(f"✅ Combined {len(all_problems)} problems from {len(datasets)} datasets")
        print(f"   Saved to: {combined_filepath}")

        # Print summary by dataset
        for dataset_name in datasets.keys():
            count = sum(1 for p in all_problems if p["source_dataset"] == dataset_name)
            print(f"   {dataset_name}: {count} problems")

    else:
        raise RuntimeError("No problems were successfully downloaded")

    return combined_filepath