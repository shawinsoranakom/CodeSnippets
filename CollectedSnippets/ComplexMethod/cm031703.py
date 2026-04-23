def writeline(self, line: str) -> None:
        self.line_number += 1
        line = line.strip()

        def pop_stack() -> TokenAndCondition:
            if not self.stack:
                self.fail(f"#{token} without matching #if / #ifdef / #ifndef!")
            return self.stack.pop()

        if self.continuation:
            line = self.continuation + line
            self.continuation = None

        if not line:
            return

        if line.endswith('\\'):
            self.continuation = line[:-1].rstrip() + " "
            return

        # we have to ignore preprocessor commands inside comments
        #
        # we also have to handle this:
        #     /* start
        #     ...
        #     */   /*    <-- tricky!
        #     ...
        #     */
        # and this:
        #     /* start
        #     ...
        #     */   /* also tricky! */
        if self.in_comment:
            if '*/' in line:
                # snip out the comment and continue
                #
                # GCC allows
                #    /* comment
                #    */ #include <stdio.h>
                # maybe other compilers too?
                _, _, line = line.partition('*/')
                self.in_comment = False

        while True:
            if '/*' in line:
                if self.in_comment:
                    self.fail("Nested block comment!")

                before, _, remainder = line.partition('/*')
                comment, comment_ends, after = remainder.partition('*/')
                if comment_ends:
                    # snip out the comment
                    line = before.rstrip() + ' ' + after.lstrip()
                    continue
                # comment continues to eol
                self.in_comment = True
                line = before.rstrip()
            break

        # we actually have some // comments
        # (but block comments take precedence)
        before, line_comment, comment = line.partition('//')
        if line_comment:
            line = before.rstrip()

        if self.in_comment:
            return

        if not line.startswith('#'):
            return

        line = line[1:].lstrip()
        assert line

        fields = line.split()
        token = fields[0].lower()
        condition = ' '.join(fields[1:]).strip()

        if token in {'if', 'ifdef', 'ifndef', 'elif'}:
            if not condition:
                self.fail(f"Invalid format for #{token} line: no argument!")
            if token in {'if', 'elif'}:
                if not is_a_simple_defined(condition):
                    condition = "(" + condition + ")"
                if token == 'elif':
                    previous_token, previous_condition = pop_stack()
                    self.stack.append((previous_token, negate(previous_condition)))
            else:
                fields = condition.split()
                if len(fields) != 1:
                    self.fail(f"Invalid format for #{token} line: "
                              "should be exactly one argument!")
                symbol = fields[0]
                condition = 'defined(' + symbol + ')'
                if token == 'ifndef':
                    condition = '!' + condition
                token = 'if'

            self.stack.append((token, condition))

        elif token == 'else':
            previous_token, previous_condition = pop_stack()
            self.stack.append((previous_token, negate(previous_condition)))

        elif token == 'endif':
            while pop_stack()[0] != 'if':
                pass

        else:
            return

        if self.verbose:
            print(self.status())