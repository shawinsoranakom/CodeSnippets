def load_data(self, data_path: str) -> list:
        """
        从json文件中读取出 文本行的坐标和gt，字符的坐标和gt
        :param data_path:
        :return:
        """
        data_list = []
        for path in data_path:
            content = load(path)
            for gt in tqdm(content["data_list"], desc="read file {}".format(path)):
                img_path = os.path.join(content["data_root"], gt["img_name"])
                polygons = []
                texts = []
                illegibility_list = []
                language_list = []
                for annotation in gt["annotations"]:
                    if len(annotation["polygon"]) == 0 or len(annotation["text"]) == 0:
                        continue
                    if len(annotation["text"]) > 1 and self.expand_one_char:
                        annotation["polygon"] = expand_polygon(annotation["polygon"])
                    polygons.append(annotation["polygon"])
                    texts.append(annotation["text"])
                    illegibility_list.append(annotation["illegibility"])
                    language_list.append(annotation["language"])
                    if self.load_char_annotation:
                        for char_annotation in annotation["chars"]:
                            if (
                                len(char_annotation["polygon"]) == 0
                                or len(char_annotation["char"]) == 0
                            ):
                                continue
                            polygons.append(char_annotation["polygon"])
                            texts.append(char_annotation["char"])
                            illegibility_list.append(char_annotation["illegibility"])
                            language_list.append(char_annotation["language"])
                data_list.append(
                    {
                        "img_path": img_path,
                        "img_name": gt["img_name"],
                        "text_polys": np.array(polygons),
                        "texts": texts,
                        "ignore_tags": illegibility_list,
                    }
                )
        return data_list