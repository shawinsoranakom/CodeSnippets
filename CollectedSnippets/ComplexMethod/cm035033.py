def __call__(self, data):
        import json

        label = data["label"]
        annotations = json.loads(label)
        boxes, texts, text_inds, labels, edges = [], [], [], [], []
        for ann in annotations:
            box = ann["points"]
            x_list = [box[i][0] for i in range(4)]
            y_list = [box[i][1] for i in range(4)]
            sorted_x_list, sorted_y_list = self.sort_vertex(x_list, y_list)
            sorted_box = []
            for x, y in zip(sorted_x_list, sorted_y_list):
                sorted_box.append(x)
                sorted_box.append(y)
            boxes.append(sorted_box)
            text = ann["transcription"]
            texts.append(ann["transcription"])
            text_ind = [self.dict[c] for c in text if c in self.dict]
            text_inds.append(text_ind)
            if "label" in ann.keys():
                labels.append(self.label2classid_map[ann["label"]])
            elif "key_cls" in ann.keys():
                labels.append(ann["key_cls"])
            else:
                raise ValueError(
                    "Cannot found 'key_cls' in ann.keys(), please check your training annotation."
                )
            edges.append(ann.get("edge", 0))
        ann_infos = dict(
            image=data["image"],
            points=boxes,
            texts=texts,
            text_inds=text_inds,
            edges=edges,
            labels=labels,
        )

        return self.list_to_numpy(ann_infos)