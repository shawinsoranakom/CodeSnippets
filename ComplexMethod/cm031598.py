def complexSum(self, sum, name):
        self.funcHeader(name)
        self.emit("PyObject *tmp = NULL;", 1)
        self.emit("PyObject *tp;", 1)
        for a in sum.attributes:
            self.visitAttributeDeclaration(a, name, sum=sum)
        self.emit("", 0)
        # XXX: should we only do this for 'expr'?
        self.emit("if (obj == Py_None) {", 1)
        self.emit("*out = NULL;", 2)
        self.emit("return 0;", 2)
        self.emit("}", 1)
        for a in sum.attributes:
            self.visitField(a, name, sum=sum, depth=1)
        for t in sum.types:
            self.emit("tp = state->%s_type;" % (t.name,), 1)
            self.emit("isinstance = PyObject_IsInstance(obj, tp);", 1)
            self.emit("if (isinstance == -1) {", 1)
            self.emit("return -1;", 2)
            self.emit("}", 1)
            self.emit("if (isinstance) {", 1)
            for f in t.fields:
                self.visitFieldDeclaration(f, t.name, sum=sum, depth=2)
            self.emit("", 0)
            for f in t.fields:
                self.visitField(f, t.name, sum=sum, depth=2)
            args = [f.name for f in t.fields] + [a.name for a in sum.attributes]
            self.emit("*out = %s(%s);" % (ast_func_name(t.name), self.buildArgs(args)), 2)
            self.emit("if (*out == NULL) goto failed;", 2)
            self.emit("return 0;", 2)
            self.emit("}", 1)
        self.sumTrailer(name, True)