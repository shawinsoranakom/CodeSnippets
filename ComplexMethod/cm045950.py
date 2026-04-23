def get_beg_end_flag_idx(self, beg_or_end, char_or_elem):
        if char_or_elem == "char":
            if beg_or_end == "beg":
                idx = self.dict_character[self.beg_str]
            elif beg_or_end == "end":
                idx = self.dict_character[self.end_str]
            else:
                assert False, "Unsupport type %s in get_beg_end_flag_idx of char" \
                              % beg_or_end
        elif char_or_elem == "elem":
            if beg_or_end == "beg":
                idx = self.dict_elem[self.beg_str]
            elif beg_or_end == "end":
                idx = self.dict_elem[self.end_str]
            else:
                assert False, "Unsupport type %s in get_beg_end_flag_idx of elem" \
                              % beg_or_end
        else:
            assert False, "Unsupport type %s in char_or_elem" \
                          % char_or_elem
        return idx