def lookup(self, tk, topn=8):
        if not tk or not isinstance(tk, str):
            return []

        # 1) Check the custom dictionary first (both keys and tk are already lowercase)
        self.lookup_num += 1
        self.load()
        key = re.sub(r"[ \t]+", " ", tk.strip())
        res = self.dictionary.get(key, [])
        if isinstance(res, str):
            res = [res]
        if res:  # Found in dictionary → return directly
            return res[:topn]

        # 2) If not found and tk is purely alphabetical → fallback to WordNet
        if re.fullmatch(r"[a-z]+", tk):
            wn_set = {
                re.sub("_", " ", syn.name().split(".")[0])
                for syn in wordnet.synsets(tk)
            }
            wn_set.discard(tk)  # Remove the original token itself
            wn_res = [t for t in wn_set if t]
            return wn_res[:topn]

        # 3) Nothing found in either source
        return []