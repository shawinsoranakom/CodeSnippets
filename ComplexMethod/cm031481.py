def home_callback(self, event):
        if (event.state & 4) != 0 and event.keysym == "Home":
            # state&4==Control. If <Control-Home>, use the Tk binding.
            return None
        if self.text.index("iomark") and \
           self.text.compare("iomark", "<=", "insert lineend") and \
           self.text.compare("insert linestart", "<=", "iomark"):
            # In Shell on input line, go to just after prompt
            insertpt = int(self.text.index("iomark").split(".")[1])
        else:
            line = self.text.get("insert linestart", "insert lineend")
            for insertpt in range(len(line)):
                if line[insertpt] not in (' ','\t'):
                    break
            else:
                insertpt=len(line)
        lineat = int(self.text.index("insert").split('.')[1])
        if insertpt == lineat:
            insertpt = 0
        dest = "insert linestart+"+str(insertpt)+"c"
        if (event.state&1) == 0:
            # shift was not pressed
            self.text.tag_remove("sel", "1.0", "end")
        else:
            if not self.text.index("sel.first"):
                # there was no previous selection
                self.text.mark_set("my_anchor", "insert")
            else:
                if self.text.compare(self.text.index("sel.first"), "<",
                                     self.text.index("insert")):
                    self.text.mark_set("my_anchor", "sel.first") # extend back
                else:
                    self.text.mark_set("my_anchor", "sel.last") # extend forward
            first = self.text.index(dest)
            last = self.text.index("my_anchor")
            if self.text.compare(first,">",last):
                first,last = last,first
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", first, last)
        self.text.mark_set("insert", dest)
        self.text.see("insert")
        return "break"