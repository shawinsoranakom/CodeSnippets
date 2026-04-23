def pack_widget_clones(self, widget_dicts, old_children=None, new_children=None):
        """ Recursively pass through the list of widgets creating clones and packing all
        children.

        Widgets cannot be given a new parent so we need to clone them and then pack the
        new widgets.

        Parameters
        ----------
        widget_dicts: list
            List of dictionaries, in appearance order, of widget information for cloning widgets
        old_childen: list, optional
            Used for recursion. Leave at ``None``
        new_childen: list, optional
            Used for recursion. Leave at ``None``
        """
        for widget_dict in widget_dicts:
            logger.debug("Cloning widget: %s", widget_dict)
            old_children = [] if old_children is None else old_children
            new_children = [] if new_children is None else new_children
            if widget_dict.get("parent", None) is not None:
                parent = new_children[old_children.index(widget_dict["parent"])]
                logger.trace("old parent: '%s', new_parent: '%s'", widget_dict["parent"], parent)
            else:
                # Get the next sub-frame if this doesn't have a logged parent
                parent = self.subframe
            clone = widget_dict["class"](parent,
                                         name=widget_dict["name"],
                                         **widget_dict["custom_kwargs"])
            if widget_dict["config"] is not None:
                clone.configure(**widget_dict["config"])
            if widget_dict["tooltip"] is not None:
                Tooltip(clone, **widget_dict["tooltip"])
            rc_menu = widget_dict["rc_menu"]
            if rc_menu is not None:
                # Re-initialize for new widget and bind
                rc_menu.__init__(widget=clone)  # pylint:disable=unnecessary-dunder-call
                rc_menu.cm_bind()
            clone.pack(**widget_dict["pack_info"])

            # Handle ToggledFrame sub-frames. If the parent is not set to expanded, then we need to
            # hide the sub-frame
            if clone.winfo_name() == "toggledframe_subframe":
                toggle_frame = clone.nametowidget(clone.winfo_parent())
                if not toggle_frame.is_expanded:
                    logger.debug("Hiding minimized toggle box: %s", clone)
                    clone.pack_forget()

            old_children.append(widget_dict["id"])
            new_children.append(clone)
            if widget_dict.get("children", None) is not None:
                self.pack_widget_clones(widget_dict["children"], old_children, new_children)