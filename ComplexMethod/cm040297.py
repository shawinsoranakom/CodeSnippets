def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        def handle_value(k):
            is_zero_dim_ndarray = isinstance(k, np.ndarray) and k.ndim == 0
            if isinstance(k, str):
                return k
            elif (
                isinstance(k, collections.abc.Iterable)
                and not is_zero_dim_ndarray
            ):
                return f'"[{", ".join(map(str, k))}]"'
            else:
                return k

        if self.keys is None:
            self.keys = sorted(logs.keys())

            val_keys_found = False
            for key in self.keys:
                if key.startswith("val_"):
                    val_keys_found = True
                    break
            if not val_keys_found and self.keys:
                self.keys.extend([f"val_{k}" for k in self.keys])

        if not self.writer:

            class CustomDialect(csv.excel):
                delimiter = self.sep

            fieldnames = ["epoch"] + (self.keys or [])

            self.writer = csv.DictWriter(
                self.csv_file, fieldnames=fieldnames, dialect=CustomDialect
            )
            if self.append_header:
                self.writer.writeheader()

        row_dict = collections.OrderedDict({"epoch": epoch})
        row_dict.update(
            (key, handle_value(logs.get(key, "NA"))) for key in self.keys
        )
        self.writer.writerow(row_dict)
        self.csv_file.flush()