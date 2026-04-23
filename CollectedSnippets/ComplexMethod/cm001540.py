def create_html(self, tabname, *, empty=False):
        """Generates an HTML string for the current pane.

        The generated HTML uses `extra-networks-pane.html` as a template.

        Args:
            tabname: The name of the active tab.
            empty: create an empty HTML page with no items

        Returns:
            HTML formatted string.
        """
        self.lister.reset()
        self.metadata = {}

        items_list = [] if empty else self.list_items()
        self.items = {x["name"]: x for x in items_list}

        # Populate the instance metadata for each item.
        for item in self.items.values():
            metadata = item.get("metadata")
            if metadata:
                self.metadata[item["name"]] = metadata

            if "user_metadata" not in item:
                self.read_user_metadata(item)

        show_tree = shared.opts.extra_networks_tree_view_default_enabled

        page_params = {
            "tabname": tabname,
            "extra_networks_tabname": self.extra_networks_tabname,
            "data_sortdir": shared.opts.extra_networks_card_order,
            "sort_path_active": ' extra-network-control--enabled' if shared.opts.extra_networks_card_order_field == 'Path' else '',
            "sort_name_active": ' extra-network-control--enabled' if shared.opts.extra_networks_card_order_field == 'Name' else '',
            "sort_date_created_active": ' extra-network-control--enabled' if shared.opts.extra_networks_card_order_field == 'Date Created' else '',
            "sort_date_modified_active": ' extra-network-control--enabled' if shared.opts.extra_networks_card_order_field == 'Date Modified' else '',
            "tree_view_btn_extra_class": "extra-network-control--enabled" if show_tree else "",
            "items_html": self.create_card_view_html(tabname, none_message="Loading..." if empty else None),
            "extra_networks_tree_view_default_width": shared.opts.extra_networks_tree_view_default_width,
            "tree_view_div_default_display_class": "" if show_tree else "extra-network-dirs-hidden",
        }

        if shared.opts.extra_networks_tree_view_style == "Tree":
            pane_content = self.pane_content_tree_tpl.format(**page_params, tree_html=self.create_tree_view_html(tabname))
        else:
            pane_content = self.pane_content_dirs_tpl.format(**page_params, dirs_html=self.create_dirs_view_html(tabname))

        return self.pane_tpl.format(**page_params, pane_content=pane_content)