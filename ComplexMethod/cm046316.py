def get_dataset(self):
        """Get train and validation datasets from data dictionary.

        Returns:
            (dict): A dictionary containing the training/validation/test dataset and category names.
        """
        try:
            # Convert ul:// platform URIs and NDJSON files to local dataset format first
            data_str = str(self.args.data)
            if data_str.endswith(".ndjson") or (data_str.startswith("ul://") and "/datasets/" in data_str):
                import asyncio

                from ultralytics.data.converter import convert_ndjson_to_yolo
                from ultralytics.utils.checks import check_file

                self.args.data = str(asyncio.run(convert_ndjson_to_yolo(check_file(self.args.data))))

            # Task-specific dataset checking
            if self.args.task == "classify":
                data = check_cls_dataset(self.args.data)
            elif str(self.args.data).rsplit(".", 1)[-1] in {"yaml", "yml"} or self.args.task in {
                "detect",
                "segment",
                "pose",
                "obb",
            }:
                data = check_det_dataset(self.args.data)
                if "yaml_file" in data:
                    self.args.data = data["yaml_file"]  # for validating 'yolo train data=url.zip' usage
        except Exception as e:
            raise RuntimeError(emojis(f"Dataset '{clean_url(self.args.data)}' error ❌ {e}")) from e
        if self.args.single_cls:
            LOGGER.info("Overriding class names with single class.")
            data["names"] = {0: "item"}
            data["nc"] = 1
        return data