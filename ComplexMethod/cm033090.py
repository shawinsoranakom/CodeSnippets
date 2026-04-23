def crop(self, text: str, ZM: int = 1, need_position: bool = False):
        imgs = []
        poss = self.extract_positions(text)
        if not poss:
            return (None, None) if need_position else None

        GAP = 6
        pos = poss[0]
        poss.insert(0, ([pos[0][0]], pos[1], pos[2], max(0, pos[3] - 120), max(pos[3] - GAP, 0)))
        pos = poss[-1]
        poss.append(([pos[0][-1]], pos[1], pos[2], min(self.page_images[pos[0][-1]].size[1], pos[4] + GAP), min(self.page_images[pos[0][-1]].size[1], pos[4] + 120)))
        positions = []
        for ii, (pns, left, right, top, bottom) in enumerate(poss):
            if bottom <= top:
                bottom = top + 4
            img0 = self.page_images[pns[0]]
            x0, y0, x1, y1 = int(left), int(top), int(right), int(min(bottom, img0.size[1]))

            crop0 = img0.crop((x0, y0, x1, y1))
            imgs.append(crop0)
            if 0 < ii < len(poss)-1:
                positions.append((pns[0] + self.page_from, x0, x1, y0, y1))
            remain_bottom = bottom - img0.size[1]
            for pn in pns[1:]:
                if remain_bottom <= 0:
                    break
                page = self.page_images[pn]
                x0, y0, x1, y1 = int(left), 0, int(right), int(min(remain_bottom, page.size[1]))
                cimgp = page.crop((x0, y0, x1, y1))
                imgs.append(cimgp)
                if 0 < ii < len(poss) - 1:
                    positions.append((pn + self.page_from, x0, x1, y0, y1))
                remain_bottom -= page.size[1]

        if not imgs:
            return (None, None) if need_position else None

        height = sum(i.size[1] + GAP for i in imgs)
        width = max(i.size[0] for i in imgs)
        pic = Image.new("RGB", (width, int(height)), (245, 245, 245))
        h = 0
        for ii, img in enumerate(imgs):
            if ii == 0 or ii + 1 == len(imgs):
                img = img.convert("RGBA")
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                overlay.putalpha(128)
                img = Image.alpha_composite(img, overlay).convert("RGB")
            pic.paste(img, (0, int(h)))
            h += img.size[1] + GAP

        return (pic, positions) if need_position else pic