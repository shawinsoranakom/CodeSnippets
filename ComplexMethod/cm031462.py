def __init__(self, editwin, index):
        "To initialize, analyze the surroundings of the given index."

        self.editwin = editwin
        self.text = text = editwin.text

        parser = pyparse.Parser(editwin.indentwidth, editwin.tabwidth)

        def index2line(index):
            return int(float(index))
        lno = index2line(text.index(index))

        if not editwin.prompt_last_line:
            for context in editwin.num_context_lines:
                startat = max(lno - context, 1)
                startatindex = repr(startat) + ".0"
                stopatindex = "%d.end" % lno
                # We add the newline because PyParse requires a newline
                # at end. We add a space so that index won't be at end
                # of line, so that its status will be the same as the
                # char before it, if should.
                parser.set_code(text.get(startatindex, stopatindex)+' \n')
                bod = parser.find_good_parse_start(
                          editwin._build_char_in_string_func(startatindex))
                if bod is not None or startat == 1:
                    break
            parser.set_lo(bod or 0)
        else:
            r = text.tag_prevrange("console", index)
            if r:
                startatindex = r[1]
            else:
                startatindex = "1.0"
            stopatindex = "%d.end" % lno
            # We add the newline because PyParse requires it. We add a
            # space so that index won't be at end of line, so that its
            # status will be the same as the char before it, if should.
            parser.set_code(text.get(startatindex, stopatindex)+' \n')
            parser.set_lo(0)

        # We want what the parser has, minus the last newline and space.
        self.rawtext = parser.code[:-2]
        # Parser.code apparently preserves the statement we are in, so
        # that stopatindex can be used to synchronize the string with
        # the text box indices.
        self.stopatindex = stopatindex
        self.bracketing = parser.get_last_stmt_bracketing()
        # find which pairs of bracketing are openers. These always
        # correspond to a character of rawtext.
        self.isopener = [i>0 and self.bracketing[i][1] >
                         self.bracketing[i-1][1]
                         for i in range(len(self.bracketing))]

        self.set_index(index)