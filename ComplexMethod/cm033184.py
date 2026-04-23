def __call__(self, image_list, ocr_res, scale_factor=3, thr=0.2, batch_size=16, drop=True):
        import re
        from collections import Counter

        assert len(image_list) == len(ocr_res)

        images = [np.array(im) if not isinstance(im, np.ndarray) else im for im in image_list]
        layouts_all_pages = []  # list of list[{"type","score","bbox":[x1,y1,x2,y2]}]

        conf_thr = max(thr, 0.08)

        batch_loop_cnt = math.ceil(float(len(images)) / batch_size)
        for bi in range(batch_loop_cnt):
            s = bi * batch_size
            e = min((bi + 1) * batch_size, len(images))
            batch_images = images[s:e]

            inputs_list = self.preprocess(batch_images)
            logging.debug("preprocess done")

            for ins in inputs_list:
                feeds = [ins["image"]]
                out_list = self.session.infer(feeds=feeds, mode="static")

                for out in out_list:
                    lts = self.postprocess(out, ins, conf_thr)

                    page_lts = []
                    for b in lts:
                        if float(b["score"]) >= 0.4 or b["type"] not in self.garbage_layouts:
                            x0, y0, x1, y1 = b["bbox"]
                            page_lts.append(
                                {
                                    "type": b["type"],
                                    "score": float(b["score"]),
                                    "x0": float(x0) / scale_factor,
                                    "x1": float(x1) / scale_factor,
                                    "top": float(y0) / scale_factor,
                                    "bottom": float(y1) / scale_factor,
                                    "page_number": len(layouts_all_pages),
                                }
                            )
                    layouts_all_pages.append(page_lts)

        def _is_garbage_text(box):
            patt = [r"^•+$", r"^[0-9]{1,2} / ?[0-9]{1,2}$", r"^[0-9]{1,2} of [0-9]{1,2}$", r"^http://[^ ]{12,}", r"\(cid *: *[0-9]+ *\)"]
            return any(re.search(p, box.get("text", "")) for p in patt)

        boxes_out = []
        page_layout = []
        garbages = {}

        for pn, lts in enumerate(layouts_all_pages):
            if lts:
                avg_h = np.mean([lt["bottom"] - lt["top"] for lt in lts])
                lts = self.sort_Y_firstly(lts, avg_h / 2 if avg_h > 0 else 0)

            bxs = ocr_res[pn]
            lts = self.layouts_cleanup(bxs, lts)
            page_layout.append(lts)

            def _tag_layout(ty):
                nonlocal bxs, lts
                lts_of_ty = [lt for lt in lts if lt["type"] == ty]
                i = 0
                while i < len(bxs):
                    if bxs[i].get("layout_type"):
                        i += 1
                        continue
                    if _is_garbage_text(bxs[i]):
                        bxs.pop(i)
                        continue

                    ii = self.find_overlapped_with_threshold(bxs[i], lts_of_ty, thr=0.4)
                    if ii is None:
                        bxs[i]["layout_type"] = ""
                        i += 1
                        continue

                    lts_of_ty[ii]["visited"] = True

                    keep_feats = [
                        lts_of_ty[ii]["type"] == "footer" and bxs[i]["bottom"] < image_list[pn].shape[0] * 0.9 / scale_factor,
                        lts_of_ty[ii]["type"] == "header" and bxs[i]["top"] > image_list[pn].shape[0] * 0.1 / scale_factor,
                    ]
                    if drop and lts_of_ty[ii]["type"] in self.garbage_layouts and not any(keep_feats):
                        garbages.setdefault(lts_of_ty[ii]["type"], []).append(bxs[i].get("text", ""))
                        bxs.pop(i)
                        continue

                    bxs[i]["layoutno"] = f"{ty}-{ii}"
                    bxs[i]["layout_type"] = lts_of_ty[ii]["type"] if lts_of_ty[ii]["type"] != "equation" else "figure"
                    i += 1

            for ty in ["footer", "header", "reference", "figure caption", "table caption", "title", "table", "text", "figure", "equation"]:
                _tag_layout(ty)

            figs = [lt for lt in lts if lt["type"] in ["figure", "equation"]]
            for i, lt in enumerate(figs):
                if lt.get("visited"):
                    continue
                lt = deepcopy(lt)
                lt.pop("type", None)
                lt["text"] = ""
                lt["layout_type"] = "figure"
                lt["layoutno"] = f"figure-{i}"
                bxs.append(lt)

            boxes_out.extend(bxs)

        garbag_set = set()
        for k, lst in garbages.items():
            cnt = Counter(lst)
            for g, c in cnt.items():
                if c > 1:
                    garbag_set.add(g)

        ocr_res_new = [b for b in boxes_out if b["text"].strip() not in garbag_set]
        return ocr_res_new, page_layout