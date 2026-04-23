def __call__(self, image_list, ocr_res, scale_factor=3, thr=0.2, batch_size=16, drop=True):
        def __is_garbage(b):
            patt = [r"\(cid\s*:\s*\d+\s*\)"]
            return any([re.search(p, b.get("text", "")) for p in patt])

        if self.client:
            layouts = self.client.predict(image_list)
        else:
            layouts = super().__call__(image_list, thr, batch_size)
        # save_results(image_list, layouts, self.labels, output_dir='output/', threshold=0.7)
        assert len(image_list) == len(ocr_res)
        # Tag layout type
        boxes = []
        assert len(image_list) == len(layouts)
        garbages = {}
        page_layout = []
        for pn, lts in enumerate(layouts):
            bxs = ocr_res[pn]
            lts = [
                {
                    "type": b["type"],
                    "score": float(b["score"]),
                    "x0": b["bbox"][0] / scale_factor,
                    "x1": b["bbox"][2] / scale_factor,
                    "top": b["bbox"][1] / scale_factor,
                    "bottom": b["bbox"][-1] / scale_factor,
                    "page_number": pn,
                }
                for b in lts
                if float(b["score"]) >= 0.4 or b["type"] not in self.garbage_layouts
            ]
            lts = self.sort_Y_firstly(lts, np.mean([lt["bottom"] - lt["top"] for lt in lts]) / 2)
            lts = self.layouts_cleanup(bxs, lts)
            page_layout.append(lts)

            def findLayout(ty):
                nonlocal bxs, lts, self
                lts_ = [lt for lt in lts if lt["type"] == ty]
                i = 0
                while i < len(bxs):
                    if bxs[i].get("layout_type"):
                        i += 1
                        continue
                    if __is_garbage(bxs[i]):
                        bxs.pop(i)
                        continue

                    ii = self.find_overlapped_with_threshold(bxs[i], lts_, thr=0.4)
                    if ii is None:
                        bxs[i]["layout_type"] = ""
                        i += 1
                        continue
                    lts_[ii]["visited"] = True
                    keep_feats = [
                        lts_[ii]["type"] == "footer" and bxs[i]["bottom"] < image_list[pn].size[1] * 0.9 / scale_factor,
                        lts_[ii]["type"] == "header" and bxs[i]["top"] > image_list[pn].size[1] * 0.1 / scale_factor,
                    ]
                    if drop and lts_[ii]["type"] in self.garbage_layouts and not any(keep_feats):
                        if lts_[ii]["type"] not in garbages:
                            garbages[lts_[ii]["type"]] = []
                        garbages[lts_[ii]["type"]].append(bxs[i]["text"])
                        bxs.pop(i)
                        continue

                    bxs[i]["layoutno"] = f"{ty}-{ii}"
                    bxs[i]["layout_type"] = lts_[ii]["type"] if lts_[ii]["type"] != "equation" else "figure"
                    i += 1

            for lt in ["footer", "header", "reference", "figure caption", "table caption", "title", "table", "text", "figure", "equation"]:
                findLayout(lt)

            # add box to figure layouts which has not text box
            for i, lt in enumerate([lt for lt in lts if lt["type"] in ["figure", "equation"]]):
                if lt.get("visited"):
                    continue
                lt = deepcopy(lt)
                del lt["type"]
                lt["text"] = ""
                lt["layout_type"] = "figure"
                lt["layoutno"] = f"figure-{i}"
                bxs.append(lt)

            boxes.extend(bxs)

        ocr_res = boxes

        garbag_set = set()
        for k in garbages.keys():
            garbages[k] = Counter(garbages[k])
            for g, c in garbages[k].items():
                if c > 1:
                    garbag_set.add(g)

        ocr_res = [b for b in ocr_res if b["text"].strip() not in garbag_set]
        return ocr_res, page_layout