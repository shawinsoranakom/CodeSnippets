def compare(self, index1, op, index2):
        line1, char1 = self._decode(index1)
        line2, char2 = self._decode(index2)
        if op == '<':
            return line1 < line2 or line1 == line2 and char1 < char2
        elif op == '<=':
            return line1 < line2 or line1 == line2 and char1 <= char2
        elif op == '>':
            return line1 > line2 or line1 == line2 and char1 > char2
        elif op == '>=':
            return line1 > line2 or line1 == line2 and char1 >= char2
        elif op == '==':
            return line1 == line2 and char1 == char2
        elif op == '!=':
            return line1 != line2 or  char1 != char2
        else:
            raise TclError('''bad comparison operator "%s": '''
                                  '''must be <, <=, ==, >=, >, or !=''' % op)