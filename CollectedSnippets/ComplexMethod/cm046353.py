def load(cls, file="data.yaml", append_filename=False):
        """Load YAML file to Python object with robust error handling.

        Args:
            file (str | Path): Path to YAML file.
            append_filename (bool): Whether to add filename to returned dict.

        Returns:
            (dict): Loaded YAML content.
        """
        instance = cls._get_instance()
        assert str(file).endswith((".yaml", ".yml")), f"Not a YAML file: {file}"

        # Read file content
        with open(file, errors="ignore", encoding="utf-8") as f:
            s = f.read()

        # Try loading YAML with fallback for problematic characters
        try:
            data = instance.yaml.load(s, Loader=instance.SafeLoader) or {}
        except Exception as e:
            # Remove problematic characters and retry
            s = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010ffff]+", "", s)
            try:
                data = instance.yaml.load(s, Loader=instance.SafeLoader) or {}
            except Exception:
                raise ValueError(
                    f"YAML syntax error in '{file}': {e}\nVerify YAML with https://ray.run/tools/yaml-formatter"
                ) from None

        # Check for accidental user-error None strings (should be 'null' in YAML)
        if "None" in data.values():
            data = {k: None if v == "None" else v for k, v in data.items()}

        if append_filename:
            data["yaml_file"] = str(file)
        return data