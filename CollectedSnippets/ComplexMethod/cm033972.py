def __getitem__(self, ch):
        # "special character" logic from pyyaml yaml.emitter.Emitter.analyze_scalar, translated to decimal
        # for perf w/ str.translate
        if (ch == 10 or
            32 <= ch <= 126 or
            ch == 133 or
            160 <= ch <= 55295 or
            57344 <= ch <= 65533 or
            65536 <= ch < 1114111)\
                and ch != 65279:
            return ch
        return None