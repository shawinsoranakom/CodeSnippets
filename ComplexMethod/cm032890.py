def df(t):
            if num_space_pattern.match(t):
                return 5
            if t in self.df:
                return self.df[t] + 3
            elif letter_pattern.match(t):
                return 300
            elif len(t) >= 4:
                s = [tt for tt in rag_tokenizer.fine_grained_tokenize(t).split() if len(tt) > 1]
                if len(s) > 1:
                    return max(3, np.min([df(tt) for tt in s]) / 6.)

            return 3