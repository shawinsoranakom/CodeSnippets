def load_dict(self, odict, force=0, rpc_client=None):
        if odict is self.prev_odict and not force:
            return
        subframe = self.subframe
        frame = self.frame
        for c in list(subframe.children.values()):
            c.destroy()
        self.prev_odict = None
        if not odict:
            l = Label(subframe, text="None")
            l.grid(row=0, column=0)
        else:
            #names = sorted(dict)
            #
            # Because of (temporary) limitations on the dict_keys type (not yet
            # public or pickleable), have the subprocess to send a list of
            # keys, not a dict_keys object.  sorted() will take a dict_keys
            # (no subprocess) or a list.
            #
            # There is also an obscure bug in sorted(dict) where the
            # interpreter gets into a loop requesting non-existing dict[0],
            # dict[1], dict[2], etc from the debugger_r.DictProxy.
            # TODO recheck above; see debugger_r 159ff, debugobj 60.
            keys_list = odict.keys()
            names = sorted(keys_list)

            row = 0
            for name in names:
                value = odict[name]
                svalue = self.repr.repr(value) # repr(value)
                # Strip extra quotes caused by calling repr on the (already)
                # repr'd value sent across the RPC interface:
                if rpc_client:
                    svalue = svalue[1:-1]
                l = Label(subframe, text=name)
                l.grid(row=row, column=0, sticky="nw")
                l = Entry(subframe, width=0, borderwidth=0)
                l.insert(0, svalue)
                l.grid(row=row, column=1, sticky="nw")
                row = row+1
        self.prev_odict = odict
        # XXX Could we use a <Configure> callback for the following?
        subframe.update_idletasks() # Alas!
        width = subframe.winfo_reqwidth()
        height = subframe.winfo_reqheight()
        canvas = self.canvas
        self.canvas["scrollregion"] = (0, 0, width, height)
        if height > 300:
            canvas["height"] = 300
            frame.pack(expand=1)
        else:
            canvas["height"] = height
            frame.pack(expand=0)