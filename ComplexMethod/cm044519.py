def config_cleaner(widget):
        """ Some options don't like to be copied, so this returns a cleaned
            configuration from a widget
            We use config() instead of configure() because some items (ttk Scale) do
            not populate configure()"""
        new_config = {}
        for key in widget.config():
            if key == "class":
                continue
            val = widget.cget(key)
            # Some keys default to "" but tkinter doesn't like to set config to this value
            # so skip them to use default value.
            if key in ("anchor", "justify", "compound") and val == "":
                continue
            # Following keys cannot be defined after widget is created:
            if key in ("colormap", "container", "visual"):
                continue
            val = str(val) if isinstance(val, Tcl_Obj) else val
            # Return correct command from master command dict
            val = _RECREATE_OBJECTS["commands"][val] if key == "command" and val != "" else val
            new_config[key] = val
        return new_config