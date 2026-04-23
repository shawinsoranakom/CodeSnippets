def cropout(bxs, ltype, poss):
            nonlocal ZM
            max_page_index = len(self.page_images) - 1

            def local_page_index(page_number):
                idx = page_number - 1 if page_number > 0 else 0
                if idx > max_page_index and self.page_from:
                    idx = page_number - 1 - self.page_from
                return idx

            pn = set()
            for b in bxs:
                idx = local_page_index(b["page_number"])
                if 0 <= idx <= max_page_index:
                    pn.add(idx)
                else:
                    logging.warning(
                        "Skip out-of-range page_number %s (page_from=%s, pages=%s)",
                        b.get("page_number"),
                        self.page_from,
                        len(self.page_images),
                    )

            if not pn:
                return None

            if len(pn) < 2:
                pn = list(pn)[0]
                ht = self.page_cum_height[pn]
                b = {"x0": np.min([b["x0"] for b in bxs]), "top": np.min([b["top"] for b in bxs]) - ht, "x1": np.max([b["x1"] for b in bxs]), "bottom": np.max([b["bottom"] for b in bxs]) - ht}
                louts = [layout for layout in self.page_layout[pn] if layout["type"] == ltype]
                ii = Recognizer.find_overlapped(b, louts, naive=True)
                if ii is not None:
                    b = louts[ii]
                else:
                    logging.warning(f"Missing layout match: {pn + 1},%s" % (bxs[0].get("layoutno", "")))

                left, top, right, bott = b["x0"], b["top"], b["x1"], b["bottom"]
                if right < left:
                    right = left + 1
                poss.append((pn + self.page_from, left, right, top, bott))
                return self.page_images[pn].crop((left * ZM, top * ZM, right * ZM, bott * ZM))
            pn = {}
            for b in bxs:
                p = local_page_index(b["page_number"])
                if 0 <= p <= max_page_index:
                    if p not in pn:
                        pn[p] = []
                    pn[p].append(b)
            pn = sorted(pn.items(), key=lambda x: x[0])
            imgs = [cropout(arr, ltype, poss) for p, arr in pn]
            imgs = [img for img in imgs if img is not None]
            if not imgs:
                return None
            pic = Image.new("RGB", (int(np.max([i.size[0] for i in imgs])), int(np.sum([m.size[1] for m in imgs]))), (245, 245, 245))
            height = 0
            for img in imgs:
                pic.paste(img, (0, int(height)))
                height += img.size[1]
            return pic