def _build_tree(self, parent: ttk.Frame, name: str | None) -> ttk.Treeview:
        """Build the configuration pop-up window.

        Parameters
        ----------
        parent : :class:`tkinter.ttk.Frame`
            The parent frame that holds the treeview
        name : str | None
            The name of the section that is being navigated to. Used for opening on the correct
            page in the Tree View. ``None`` if no specific area is being navigated to

        Returns
        -------
        :class:`tkinter.ttk.Treeview`
            The populated tree view
        """
        logger.debug("Building Tree View Navigator")
        tree = ttk.Treeview(parent, show="tree", style="ConfigNav.Treeview")
        data = {category: [sect.split(".") for sect in sorted(conf.sections)]
                for category, conf in get_configs().items()}
        ordered = sorted(list(data.keys()))
        categories = ["extract", "train", "convert"]
        categories += [x for x in ordered if x not in categories]

        for cat in categories:
            img = get_images().icons.get(f"settings_{cat}", "")
            text = cat.replace("_", " ").title()
            text = " " + text if img else text
            is_open = tk.TRUE if name is None or name == cat else tk.FALSE
            tree.insert("", "end", cat, text=text, image=img, open=is_open, tags="category")
            self._process_sections(tree, data[cat], cat, name == cat)

        tree.tag_configure('category', background='#DFDFDF')
        tree.tag_configure('section', background='#E8E8E8')
        tree.tag_configure('option', background='#F0F0F0')
        logger.debug("Tree View Navigator")
        return tree