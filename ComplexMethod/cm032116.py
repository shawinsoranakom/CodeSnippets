def search(self, text):
        # 逐个单词进行匹配搜索
        text = text.lower()
        found_terms = []
        n = len(text)
        max_word_wrap = 30
        for i in range(n):
            current_state = self.states
            j = i
            found = False
            while j < n + max_word_wrap and text[j] in current_state:
                current_state = current_state[text[j]]
                j += 1
                if '#' in current_state and self.is_at_word_end(text, j):
                    if current_state['#'] not in found_terms:
                        if found: found_terms.pop(-1)   # greedy search for longer matched term
                        found_terms.append(current_state['#'])
                        found = True
        return found_terms