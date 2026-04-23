def __getitem__(self, index):
        try:
            data = copy.deepcopy(self.data_list[index])
            im = cv2.imread(data["img_path"], 1 if self.img_mode != "GRAY" else 0)
            if self.img_mode == "RGB":
                im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            data["img"] = im
            data["shape"] = [im.shape[0], im.shape[1]]
            data = self.apply_pre_processes(data)

            if self.transform:
                data["img"] = self.transform(data["img"])
            data["text_polys"] = data["text_polys"].tolist()
            if len(self.filter_keys):
                data_dict = {}
                for k, v in data.items():
                    if k not in self.filter_keys:
                        data_dict[k] = v
                return data_dict
            else:
                return data
        except:
            return self.__getitem__(np.random.randint(self.__len__()))