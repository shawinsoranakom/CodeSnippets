def add_browser_buttons(self):
        """ Add correct file browser button for control """
        logger.debug("Adding browser buttons: (sysbrowser: %s", self.browser)
        frame = ttk.Frame(self.frame, style=f"{self._style}Group.TFrame")
        frame.pack(side=tk.RIGHT, padx=(0, 5))

        for browser in self.browser:
            if browser == "save":
                lbl = "save_as"
            elif browser == "load" and self.filetypes == "video":
                lbl = self.filetypes
            elif browser == "load":
                lbl = "load2"
            elif browser == "folder" and (self._opt_name.startswith(("frames", "faces"))
                                          or "input" in self._opt_name):
                lbl = "picture"
            elif browser == "folder" and "model" in self._opt_name:
                lbl = "model"
            else:
                lbl = browser
            img = get_images().icons[lbl]
            action = getattr(self, "ask_" + browser)
            cmd = partial(action, filepath=self.tk_var, filetypes=self.filetypes)
            fileopn = tk.Button(frame,
                                image=img,
                                command=cmd,
                                relief=tk.SOLID,
                                bd=1,
                                bg=get_config().user_theme["group_panel"]["button_background"],
                                cursor="hand2")
            _add_command(fileopn.cget("command"), cmd)
            fileopn.pack(padx=1, side=tk.RIGHT)
            _get_tooltip(fileopn, text=self.helptext[lbl])
            logger.debug("Added browser buttons: (action: %s, filetypes: %s",
                         action, self.filetypes)