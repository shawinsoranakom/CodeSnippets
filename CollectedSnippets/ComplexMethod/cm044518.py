def get_all_children_config(self, widget, child_list):
        """ Return all children, recursively, of given widget.

        Parameters
        ----------
        widget: tkinter widget
            The widget to recursively obtain the configurations of each child
        child_list: list
            The list of child configurations already collected

        Returns
        -------
        list
            The list of configurations for all recursive children of the given widget
         """
        unpack = set()
        for child in widget.winfo_children():
            # Hidden Toggle Frame boxes need to be mapped
            if child.winfo_ismapped() or "toggledframe_subframe" in str(child):
                not_mapped = not child.winfo_ismapped()
                # ToggleFrame is a custom widget that creates it's own children and handles
                # bindings on the headers, to auto-hide the contents. To ensure that all child
                # information (specifically pack information) can be collected, we need to pack
                # any hidden sub-frames. These are then hidden again once collected.
                if not_mapped and (child.winfo_name() == "toggledframe_subframe" or
                                   child.winfo_name() == "chkbuttons"):
                    child.pack(fill=tk.X, expand=True)
                    child.update_idletasks()  # Updates the packing info of children
                    unpack.add(child)

                if child.winfo_name().startswith("toggledframe_header"):
                    # Headers should be entirely handled by parent widget
                    continue

                child_list.append({
                    "class": child.__class__,
                    "id": str(child),
                    "tooltip": _RECREATE_OBJECTS["tooltips"].get(str(child), None),
                    "rc_menu": _RECREATE_OBJECTS["contextmenus"].get(str(child), None),
                    "pack_info": self.pack_config_cleaner(child),
                    "name": child.winfo_name(),
                    "config": self.config_cleaner(child),
                    "parent": child.winfo_parent(),
                    "custom_kwargs": self._custom_kwargs(child)})
            self.get_all_children_config(child, child_list)

        # Re-hide any toggle frames that were expanded
        for hide in unpack:
            hide.pack_forget()
            hide.update_idletasks()
        return child_list