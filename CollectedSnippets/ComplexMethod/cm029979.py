def visit_arguments(self, node):
        first = True
        # normal arguments
        all_args = node.posonlyargs + node.args
        defaults = [None] * (len(all_args) - len(node.defaults)) + node.defaults
        for index, elements in enumerate(zip(all_args, defaults), 1):
            a, d = elements
            if first:
                first = False
            else:
                self.write(", ")
            self.traverse(a)
            if d:
                self.write("=")
                self.traverse(d)
            if index == len(node.posonlyargs):
                self.write(", /")

        # varargs, or bare '*' if no varargs but keyword-only arguments present
        if node.vararg or node.kwonlyargs:
            if first:
                first = False
            else:
                self.write(", ")
            self.write("*")
            if node.vararg:
                self.write(node.vararg.arg)
                if node.vararg.annotation:
                    self.write(": ")
                    self.traverse(node.vararg.annotation)

        # keyword-only arguments
        if node.kwonlyargs:
            for a, d in zip(node.kwonlyargs, node.kw_defaults):
                self.write(", ")
                self.traverse(a)
                if d:
                    self.write("=")
                    self.traverse(d)

        # kwargs
        if node.kwarg:
            if first:
                first = False
            else:
                self.write(", ")
            self.write("**" + node.kwarg.arg)
            if node.kwarg.annotation:
                self.write(": ")
                self.traverse(node.kwarg.annotation)