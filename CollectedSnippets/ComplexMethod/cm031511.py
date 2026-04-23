def show_window(self, comp_lists, index, complete, mode, userWantsWin):
        """Show the autocomplete list, bind events.

        If complete is True, complete the text, and if there is exactly
        one matching completion, don't open a list.
        """
        # Handle the start we already have
        self.completions, self.morecompletions = comp_lists
        self.mode = mode
        self.startindex = self.widget.index(index)
        self.start = self.widget.get(self.startindex, "insert")
        if complete:
            completed = self._complete_string(self.start)
            start = self.start
            self._change_start(completed)
            i = self._binary_search(completed)
            if self.completions[i] == completed and \
               (i == len(self.completions)-1 or
                self.completions[i+1][:len(completed)] != completed):
                # There is exactly one matching completion
                return completed == start
        self.userwantswindow = userWantsWin
        self.lasttypedstart = self.start

        self.autocompletewindow = acw = Toplevel(self.widget)
        acw.withdraw()
        acw.wm_overrideredirect(1)
        try:
            # Prevent grabbing focus on macOS.
            acw.tk.call("::tk::unsupported::MacWindowStyle", "style", acw._w,
                        "help", "noActivates")
        except TclError:
            pass
        self.scrollbar = scrollbar = Scrollbar(acw, orient=VERTICAL)
        self.listbox = listbox = Listbox(acw, yscrollcommand=scrollbar.set,
                                         exportselection=False)
        for item in self.completions:
            listbox.insert(END, item)
        self.origselforeground = listbox.cget("selectforeground")
        self.origselbackground = listbox.cget("selectbackground")
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        listbox.pack(side=LEFT, fill=BOTH, expand=True)
        #acw.update_idletasks() # Need for tk8.6.8 on macOS: #40128.
        acw.lift()  # work around bug in Tk 8.5.18+ (issue #24570)

        # Initialize the listbox selection
        self.listbox.select_set(self._binary_search(self.start))
        self._selection_changed()

        # bind events
        self.hideaid = acw.bind(HIDE_VIRTUAL_EVENT_NAME, self.hide_event)
        self.hidewid = self.widget.bind(HIDE_VIRTUAL_EVENT_NAME, self.hide_event)
        acw.event_add(HIDE_VIRTUAL_EVENT_NAME, HIDE_FOCUS_OUT_SEQUENCE)
        for seq in HIDE_SEQUENCES:
            self.widget.event_add(HIDE_VIRTUAL_EVENT_NAME, seq)

        self.keypressid = self.widget.bind(KEYPRESS_VIRTUAL_EVENT_NAME,
                                           self.keypress_event)
        for seq in KEYPRESS_SEQUENCES:
            self.widget.event_add(KEYPRESS_VIRTUAL_EVENT_NAME, seq)
        self.keyreleaseid = self.widget.bind(KEYRELEASE_VIRTUAL_EVENT_NAME,
                                             self.keyrelease_event)
        self.widget.event_add(KEYRELEASE_VIRTUAL_EVENT_NAME,KEYRELEASE_SEQUENCE)
        self.listupdateid = listbox.bind(LISTUPDATE_SEQUENCE,
                                         self.listselect_event)
        self.is_configuring = False
        self.winconfigid = acw.bind(WINCONFIG_SEQUENCE, self.winconfig_event)
        self.doubleclickid = listbox.bind(DOUBLECLICK_SEQUENCE,
                                          self.doubleclick_event)
        return None