def get_ext_data(self):
        ext_data_num = 0
        for op in self.ops:
            if hasattr(op, "ext_data_num"):
                ext_data_num = getattr(op, "ext_data_num")
                break
        load_data_ops = self.ops[: self.ext_op_transform_idx]
        ext_data = []

        while len(ext_data) < ext_data_num:
            file_idx = self.data_idx_order_list[np.random.randint(self.__len__())]
            data_line = self.data_lines[file_idx]
            data_line = data_line.decode("utf-8")
            substr = data_line.strip("\n").split(self.delimiter)
            file_name = substr[0]
            file_name = self._try_parse_filename_list(file_name)
            label = substr[1]
            img_path = os.path.join(self.data_dir, file_name)
            data = {"img_path": img_path, "label": label}
            if not os.path.exists(img_path):
                continue
            with open(data["img_path"], "rb") as f:
                img = f.read()
                data["image"] = img
            data = transform(data, load_data_ops)

            if data is None:
                continue
            if "polys" in data.keys():
                if data["polys"].shape[1] != 4:
                    continue
            ext_data.append(data)
        return ext_data