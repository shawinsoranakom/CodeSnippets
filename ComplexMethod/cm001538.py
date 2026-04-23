def create_item_html(
        self,
        tabname: str,
        item: dict,
        template: Optional[str] = None,
    ) -> Union[str, dict]:
        """Generates HTML for a single ExtraNetworks Item.

        Args:
            tabname: The name of the active tab.
            item: Dictionary containing item information.
            template: Optional template string to use.

        Returns:
            If a template is passed: HTML string generated for this item.
                Can be empty if the item is not meant to be shown.
            If no template is passed: A dictionary containing the generated item's attributes.
        """
        preview = item.get("preview", None)
        style_height = f"height: {shared.opts.extra_networks_card_height}px;" if shared.opts.extra_networks_card_height else ''
        style_width = f"width: {shared.opts.extra_networks_card_width}px;" if shared.opts.extra_networks_card_width else ''
        style_font_size = f"font-size: {shared.opts.extra_networks_card_text_scale*100}%;"
        card_style = style_height + style_width + style_font_size
        background_image = f'<img src="{html.escape(preview)}" class="preview" loading="lazy">' if preview else ''

        onclick = item.get("onclick", None)
        if onclick is None:
            # Don't quote prompt/neg_prompt since they are stored as js strings already.
            onclick_js_tpl = "cardClicked('{tabname}', {prompt}, {neg_prompt}, {allow_neg});"
            onclick = onclick_js_tpl.format(
                **{
                    "tabname": tabname,
                    "prompt": item["prompt"],
                    "neg_prompt": item.get("negative_prompt", "''"),
                    "allow_neg": str(self.allow_negative_prompt).lower(),
                }
            )
            onclick = html.escape(onclick)

        btn_copy_path = self.btn_copy_path_tpl.format(**{"filename": item["filename"]})
        btn_metadata = ""
        metadata = item.get("metadata")
        if metadata:
            btn_metadata = self.btn_metadata_tpl.format(
                **{
                    "extra_networks_tabname": self.extra_networks_tabname,
                }
            )
        btn_edit_item = self.btn_edit_item_tpl.format(
            **{
                "tabname": tabname,
                "extra_networks_tabname": self.extra_networks_tabname,
            }
        )

        local_path = ""
        filename = item.get("filename", "")
        for reldir in self.allowed_directories_for_previews():
            absdir = os.path.abspath(reldir)

            if filename.startswith(absdir):
                local_path = filename[len(absdir):]

        # if this is true, the item must not be shown in the default view, and must instead only be
        # shown when searching for it
        if shared.opts.extra_networks_hidden_models == "Always":
            search_only = False
        else:
            search_only = "/." in local_path or "\\." in local_path

        if search_only and shared.opts.extra_networks_hidden_models == "Never":
            return ""

        sort_keys = " ".join(
            [
                f'data-sort-{k}="{html.escape(str(v))}"'
                for k, v in item.get("sort_keys", {}).items()
            ]
        ).strip()

        search_terms_html = ""
        search_term_template = "<span class='hidden {class}'>{search_term}</span>"
        for search_term in item.get("search_terms", []):
            search_terms_html += search_term_template.format(
                **{
                    "class": f"search_terms{' search_only' if search_only else ''}",
                    "search_term": search_term,
                }
            )

        description = (item.get("description", "") or "" if shared.opts.extra_networks_card_show_desc else "")
        if not shared.opts.extra_networks_card_description_is_html:
            description = html.escape(description)

        # Some items here might not be used depending on HTML template used.
        args = {
            "background_image": background_image,
            "card_clicked": onclick,
            "copy_path_button": btn_copy_path,
            "description": description,
            "edit_button": btn_edit_item,
            "local_preview": quote_js(item["local_preview"]),
            "metadata_button": btn_metadata,
            "name": html.escape(item["name"]),
            "prompt": item.get("prompt", None),
            "save_card_preview": html.escape(f"return saveCardPreview(event, '{tabname}', '{item['local_preview']}');"),
            "search_only": " search_only" if search_only else "",
            "search_terms": search_terms_html,
            "sort_keys": sort_keys,
            "style": card_style,
            "tabname": tabname,
            "extra_networks_tabname": self.extra_networks_tabname,
        }

        if template:
            return template.format(**args)
        else:
            return args