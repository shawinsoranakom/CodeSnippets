def add_stylesheets(self, handler):
        for stylesheet in self.feed["stylesheets"] or []:
            handler.processingInstruction("xml-stylesheet", stylesheet)