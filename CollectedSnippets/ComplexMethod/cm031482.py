def right_menu_event(self, event):
        text = self.text
        newdex = text.index(f'@{event.x},{event.y}')
        try:
            in_selection = (text.compare('sel.first', '<=', newdex) and
                           text.compare(newdex, '<=',  'sel.last'))
        except TclError:
            in_selection = False
        if not in_selection:
            text.tag_remove("sel", "1.0", "end")
            text.mark_set("insert", newdex)
        if not self.rmenu:
            self.make_rmenu()
        rmenu = self.rmenu
        self.event = event
        iswin = sys.platform[:3] == 'win'
        if iswin:
            text.config(cursor="arrow")

        for item in self.rmenu_specs:
            try:
                label, eventname, verify_state = item
            except ValueError: # see issue1207589
                continue

            if verify_state is None:
                continue
            state = getattr(self, verify_state)()
            rmenu.entryconfigure(label, state=state)

        rmenu.tk_popup(event.x_root, event.y_root)
        if iswin:
            self.text.config(cursor="ibeam")
        return "break"