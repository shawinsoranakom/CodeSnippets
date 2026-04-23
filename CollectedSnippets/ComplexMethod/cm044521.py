def build_one_control(self):
        """ Build and place the option controls """
        logger.debug("Build control: '%s')", self.option.name)
        if self.option.control == "scale":
            ctl = self.slider_control()
        elif self.option.control in ("radio", "multi"):
            ctl = self._multi_option_control(self.option.control)
        elif self.option.control == "colorchooser":
            ctl = self._color_control()
        elif self.option.control == ttk.Checkbutton:
            ctl = self.control_to_checkframe()
        else:
            ctl = self.control_to_optionsframe()
        if self.option.control != ttk.Checkbutton:
            ctl.pack(padx=5, pady=5, fill=tk.X, expand=True)
            if self.option.helptext is not None and not self.helpset:
                tooltip_kwargs = {"text": self.option.helptext}
                if self.option.sysbrowser is not None:
                    tooltip_kwargs["text_variable"] = self.option.tk_var
                _get_tooltip(ctl, **tooltip_kwargs)

        logger.debug("Built control: '%s'", self.option.name)