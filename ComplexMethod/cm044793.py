def _merge_yi(self, seg: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        new_seg = []
        i = 0
        # function 1
        while i < len(seg):
            word, pos = seg[i]
            merged = False
            if i - 1 >= 0 and word == "一" and i + 1 < len(seg):
                last = new_seg[-1] if new_seg else seg[i - 1]
                if last[0] == seg[i + 1][0] and last[1] == "v" and seg[i + 1][1] == "v":
                    combined = last[0] + "一" + seg[i + 1][0]
                    new_seg[-1] = [combined, last[1]]
                    i += 2
                    merged = True
            if not merged:
                new_seg.append([word, pos])
                i += 1
        seg = new_seg
        new_seg = []
        # function 2
        for word, pos in seg:
            if new_seg and new_seg[-1][0] == "一":
                new_seg[-1][0] = new_seg[-1][0] + word
            else:
                new_seg.append([word, pos])
        return new_seg