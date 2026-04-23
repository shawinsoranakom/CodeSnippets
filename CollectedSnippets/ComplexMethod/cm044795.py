def _merge_continuous_three_tones_2(self, seg: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        new_seg = []
        sub_finals_list = [
            lazy_pinyin(word, neutral_tone_with_five=True, style=Style.FINALS_TONE3) for (word, pos) in seg
        ]
        assert len(sub_finals_list) == len(seg)
        merge_last = [False] * len(seg)
        for i, (word, pos) in enumerate(seg):
            if (
                i - 1 >= 0
                and sub_finals_list[i - 1][-1][-1] == "3"
                and sub_finals_list[i][0][-1] == "3"
                and not merge_last[i - 1]
            ):
                # if the last word is reduplication, not merge, because reduplication need to be _neural_sandhi
                if not self._is_reduplication(seg[i - 1][0]) and len(seg[i - 1][0]) + len(seg[i][0]) <= 3:
                    new_seg[-1][0] = new_seg[-1][0] + seg[i][0]
                    merge_last[i] = True
                else:
                    new_seg.append([word, pos])
            else:
                new_seg.append([word, pos])
        return new_seg