def __call__(self, string):
        lines = string.split("\n")
        lyric_token_idx = [261]
        for line in lines:
            line = line.strip()
            if not line:
                lyric_token_idx += [2]
                continue

            lang, line = self.get_lang(line)

            if lang not in SUPPORT_LANGUAGES:
                lang = "en"
            if "zh" in lang:
                lang = "zh"
            if "spa" in lang:
                lang = "es"

            try:
                line_out = japanese_to_romaji(line)
                if line_out != line:
                    lang = "ja"
                line = line_out
            except:
                pass

            try:
                if structure_pattern.match(line):
                    token_idx = self.encode(line, "en")
                else:
                    token_idx = self.encode(line, lang)
                lyric_token_idx = lyric_token_idx + token_idx + [2]
            except Exception as e:
                logging.warning("tokenize error {} for line {} major_language {}".format(e, line, lang))
        return {"input_ids": lyric_token_idx}