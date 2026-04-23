def build_dfa(self):
        all_terms = []
        all_blacklist_terms = all_blacklist_terms_predefine

        # 将markdown格式的术语转换为Term对象
        for term_raw in black_list_ai_terms.split('\n'):
            if '|' not in term_raw: continue
            if 'AITD' not in term_raw: continue
            t = Term()
            t.id, t.words, t.translation, _, _, _, _ = term_raw.split('|')
            all_blacklist_terms.append(t.words)

        # 将markdown格式的术语转换为Term对象
        for term_raw in ai_terms_from_web.split('\n'):
            if '|' not in term_raw: continue
            if 'AITD' not in term_raw: continue
            t = Term()
            t.id, t.words, t.translation, _, _, _, _ = term_raw.split('|')
            if t.words in all_blacklist_terms: continue
            all_terms.append(t)

        # 构建DFA
        for term in all_terms:
            current_state = self.states
            for char in term.words.lower():
                if char not in current_state:
                    current_state[char] = {}
                current_state = current_state[char]
            current_state['#'] = term