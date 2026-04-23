def evaluate(self, yaml_path: str, val_log_file: str, eval_log_file: str, list_ind: int):
        """Evaluate model performance on validation results.

        Args:
            yaml_path (str): Path to the YAML configuration file.
            val_log_file (str): Path to the validation log file.
            eval_log_file (str): Path to the evaluation log file.
            list_ind (int): Index of the current dataset in the list.

        Returns:
            (float): The mean average precision (mAP) value for the evaluated model.

        Examples:
            Evaluate a model on a specific dataset
            >>> benchmark = RF100Benchmark()
            >>> benchmark.evaluate("path/to/data.yaml", "path/to/val_log.txt", "path/to/eval_log.txt", 0)
        """
        skip_symbols = ["🚀", "⚠️", "💡", "❌"]
        class_names = YAML.load(yaml_path)["names"]
        with open(val_log_file, encoding="utf-8") as f:
            lines = f.readlines()
            eval_lines = []
            for line in lines:
                if any(symbol in line for symbol in skip_symbols):
                    continue
                entries = line.split(" ")
                entries = list(filter(lambda val: val != "", entries))
                entries = [e.strip("\n") for e in entries]
                eval_lines.extend(
                    {
                        "class": entries[0],
                        "images": entries[1],
                        "targets": entries[2],
                        "precision": entries[3],
                        "recall": entries[4],
                        "map50": entries[5],
                        "map95": entries[6],
                    }
                    for e in entries
                    if e in class_names or (e == "all" and "(AP)" not in entries and "(AR)" not in entries)
                )
        map_val = 0.0
        if len(eval_lines) > 1:
            LOGGER.info("Multiple dicts found")
            for lst in eval_lines:
                if lst["class"] == "all":
                    map_val = lst["map50"]
        else:
            LOGGER.info("Single dict found")
            map_val = next(res["map50"] for res in eval_lines)

        with open(eval_log_file, "a", encoding="utf-8") as f:
            f.write(f"{self.ds_names[list_ind]}: {map_val}\n")

        return float(map_val)