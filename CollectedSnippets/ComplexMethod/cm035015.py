def __getitem__(self, properties):
        # properties is a tuple, contains (width, height, index)
        img_height = properties[1]
        idx = properties[2]
        if self.ds_width and properties[3] is not None:
            wh_ratio = properties[3]
            img_width = img_height * (
                1 if int(round(wh_ratio)) == 0 else int(round(wh_ratio))
            )
            file_idx = self.wh_ratio_sort[idx]
        else:
            file_idx = self.data_idx_order_list[idx]
            img_width = properties[0]
            wh_ratio = None

        data_line = self.data_lines[file_idx]
        try:
            data_line = data_line.decode("utf-8")
            substr = data_line.strip("\n").split(self.delimiter)
            file_name = substr[0]
            file_name = self._try_parse_filename_list(file_name)
            label = substr[1]
            img_path = os.path.join(self.data_dir, file_name)
            data = {"img_path": img_path, "label": label}
            if not os.path.exists(img_path):
                raise Exception("{} does not exist!".format(img_path))
            with open(data["img_path"], "rb") as f:
                img = f.read()
                data["image"] = img
            data["ext_data"] = self.get_ext_data()
            outs = transform(data, self.ops[:-1])
            if outs is not None:
                outs = self.resize_norm_img(outs, img_width, img_height)
                outs = transform(outs, self.ops[-1:])
        except:
            self.logger.error(
                "When parsing line {}, error happened with msg: {}".format(
                    data_line, traceback.format_exc()
                )
            )
            outs = None
        if outs is None:
            # during evaluation, we should fix the idx to get same results for many times of evaluation.
            rnd_idx = (idx + 1) % self.__len__()
            return self.__getitem__([img_width, img_height, rnd_idx, wh_ratio])
        return outs