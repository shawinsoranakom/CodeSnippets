def eval_print_amount(self, sel, list, msg):
        new_list = list
        if isinstance(sel, str):
            try:
                rex = re.compile(sel)
            except re.PatternError:
                msg += "   <Invalid regular expression %r>\n" % sel
                return new_list, msg
            new_list = []
            for func in list:
                if rex.search(func_std_string(func)):
                    new_list.append(func)
        else:
            count = len(list)
            if isinstance(sel, float) and 0.0 <= sel < 1.0:
                count = int(count * sel + .5)
                new_list = list[:count]
            elif isinstance(sel, int) and 0 <= sel < count:
                count = sel
                new_list = list[:count]
        if len(list) != len(new_list):
            msg += "   List reduced from %r to %r due to restriction <%r>\n" % (
                len(list), len(new_list), sel)

        return new_list, msg