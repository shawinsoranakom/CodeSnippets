def display_item_process(self) -> None:
        """ Add a single graph to the graph window """
        if not Session.is_training:
            logger.debug("Waiting for Session Data to become available to graph")
            self.after(1000, self.display_item_process)
            return

        existing = list(self.subnotebook_get_titles_ids().keys())

        loss_keys = self.display_item.get_loss_keys(Session.session_ids[-1])
        if not loss_keys:
            # Reload if we attempt to get loss keys before data is written
            logger.debug("Waiting for Session Data to become available to graph")
            self.after(1000, self.display_item_process)
            return

        loss_keys = [key for key in loss_keys if key != "total"]
        display_tabs = sorted(set(key[:-1].rstrip("_") for key in loss_keys))

        for loss_key in display_tabs:
            tabname = loss_key.replace("_", " ").title()
            if tabname in existing:
                continue
            logger.debug("Adding graph '%s'", tabname)

            display_keys = [key for key in loss_keys if key.startswith(loss_key)]
            data = Calculations(session_id=Session.session_ids[-1],
                                display="loss",
                                loss_keys=display_keys,
                                selections=["raw", "smoothed"],
                                smooth_amount=self.vars["smoothgraph"].get())
            self.add_child(tabname, data)