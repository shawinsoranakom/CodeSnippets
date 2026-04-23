def __call__(self, string):
        if self.special_tokens is not None:
            import re
            special_tokens_pattern = '|'.join(re.escape(token) for token in self.special_tokens.keys())
            if special_tokens_pattern and re.search(special_tokens_pattern, string):
                parts = re.split(f'({special_tokens_pattern})', string)
                result = []
                for part in parts:
                    if not part:
                        continue
                    if part in self.special_tokens:
                        result.append(self.special_tokens[part])
                    else:
                        encoded = self.tokenizer.encode(part, add_bos=False, add_eos=False)
                        result.extend(encoded)
                return {"input_ids": result}

        out = self.tokenizer.encode(string)
        return {"input_ids": out}