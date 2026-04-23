def drawtext(self):
        textx = self.x+20-1
        texty = self.y-4
        labeltext = self.item.GetLabelText()
        if labeltext:
            id = self.canvas.create_text(textx, texty, anchor="nw",
                                         text=labeltext)
            self.canvas.tag_bind(id, "<1>", self.select)
            self.canvas.tag_bind(id, "<Double-1>", self.flip)
            x0, y0, x1, y1 = self.canvas.bbox(id)
            textx = max(x1, 200) + 10
        text = self.item.GetText() or "<no text>"
        try:
            self.entry
        except AttributeError:
            pass
        else:
            self.edit_finish()
        try:
            self.label
        except AttributeError:
            # padding carefully selected (on Windows) to match Entry widget:
            self.label = Label(self.canvas, text=text, bd=0, padx=2, pady=2)
        theme = idleConf.CurrentTheme()
        if self.selected:
            self.label.configure(idleConf.GetHighlight(theme, 'hilite'))
        else:
            self.label.configure(idleConf.GetHighlight(theme, 'normal'))
        id = self.canvas.create_window(textx, texty,
                                       anchor="nw", window=self.label)
        self.label.bind("<1>", self.select_or_edit)
        self.label.bind("<Double-1>", self.flip)
        self.label.bind("<MouseWheel>", lambda e: wheel_event(e, self.canvas))
        if self.label._windowingsystem == 'x11':
            self.label.bind("<Button-4>", lambda e: wheel_event(e, self.canvas))
            self.label.bind("<Button-5>", lambda e: wheel_event(e, self.canvas))
        self.text_id = id
        if TreeNode.dy == 0:
            # The first row doesn't matter what the dy is, just measure its
            # size to get the value of the subsequent dy
            coords = self.canvas.bbox(id)
            TreeNode.dy = max(20, coords[3] - coords[1] - 3)