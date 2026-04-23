def __call__(self, images, thr=0.2):
        table_structure_recognizer_type = os.getenv("TABLE_STRUCTURE_RECOGNIZER_TYPE", "onnx").lower()
        if table_structure_recognizer_type not in ["onnx", "ascend"]:
            raise RuntimeError("Unsupported table structure recognizer type.")

        if table_structure_recognizer_type == "onnx":
            logging.debug("Using Onnx table structure recognizer")
            tbls = super().__call__(images, thr)
        else:  # ascend
            logging.debug("Using Ascend table structure recognizer")
            tbls = self._run_ascend_tsr(images, thr)

        res = []
        # align left&right for rows, align top&bottom for columns
        for tbl in tbls:
            lts = [
                {
                    "label": b["type"],
                    "score": b["score"],
                    "x0": b["bbox"][0],
                    "x1": b["bbox"][2],
                    "top": b["bbox"][1],
                    "bottom": b["bbox"][-1],
                }
                for b in tbl
            ]
            if not lts:
                continue

            left = [b["x0"] for b in lts if b["label"].find("row") > 0 or b["label"].find("header") > 0]
            right = [b["x1"] for b in lts if b["label"].find("row") > 0 or b["label"].find("header") > 0]
            if not left:
                continue
            left = np.mean(left) if len(left) > 4 else np.min(left)
            right = np.mean(right) if len(right) > 4 else np.max(right)
            for b in lts:
                if b["label"].find("row") > 0 or b["label"].find("header") > 0:
                    if b["x0"] > left:
                        b["x0"] = left
                    if b["x1"] < right:
                        b["x1"] = right

            top = [b["top"] for b in lts if b["label"] == "table column"]
            bottom = [b["bottom"] for b in lts if b["label"] == "table column"]
            if not top:
                res.append(lts)
                continue
            top = np.median(top) if len(top) > 4 else np.min(top)
            bottom = np.median(bottom) if len(bottom) > 4 else np.max(bottom)
            for b in lts:
                if b["label"] == "table column":
                    if b["top"] > top:
                        b["top"] = top
                    if b["bottom"] < bottom:
                        b["bottom"] = bottom

            res.append(lts)
        return res