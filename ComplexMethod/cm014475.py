def mask_comments(string):
        in_comment = ''
        prev_c = ''
        new_string = ''
        for c in string:
            if in_comment == '':
                # Outside comments
                if c == '/' and prev_c == '/':
                    in_comment = '//'
                elif c == '*' and prev_c == '/':
                    in_comment = '/*'
                elif c == '"' and prev_c != '\\' and prev_c != "'":
                    in_comment = '"'
            elif in_comment == '//':
                # In // xxx
                if c == '\r' or c == '\n':
                    in_comment = ''
            elif in_comment == '/*':
                # In /* xxx */
                if c == '/' and prev_c == '*':
                    in_comment = ''
            elif in_comment == '"':
                # In ""
                if c == '"' and prev_c != '\\':
                    in_comment = ''
            prev_c = c
            if in_comment == '':
                new_string += c
            else:
                new_string += 'x'
        return new_string