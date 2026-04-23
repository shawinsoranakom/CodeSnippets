def _add_transport(self):
        """ Add video transport controls """
        frame = ttk.Frame(self._transport_frame)
        frame.pack(side=tk.BOTTOM, fill=tk.X)
        icons = get_images().icons
        buttons = {}
        for action in ("play", "beginning", "prev", "next", "end", "save", "extract", "mode"):
            padx = (0, 6) if action in ("play", "prev", "mode") else (0, 0)
            side = tk.RIGHT if action in ("extract", "save", "mode") else tk.LEFT
            state = ["!disabled"] if action != "save" else ["disabled"]
            if action != "mode":
                icon = action if action != "extract" else "folder"
                wgt = ttk.Button(frame, image=icons[icon], command=self._btn_action[action])
                wgt.state(state)
            else:
                wgt = self._add_filter_section(frame)
            wgt.pack(side=side, padx=padx)
            if action != "mode":
                Tooltip(wgt, text=self._helptext[action])
            buttons[action] = wgt
        logger.debug("Transport buttons: %s", buttons)
        return buttons