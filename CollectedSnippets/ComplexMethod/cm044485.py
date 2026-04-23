def _display_preview(self) -> None:
        """ Handle the displaying of the images currently in :attr:`_preview_buffer`"""
        if self._should_shutdown:
            self._root.destroy()

        if not self._buffer.is_updated:
            self._root.after(1000, self._display_preview)
            return

        for name, image in self._buffer.get_images():
            logger.debug("Updating image: (name: '%s', shape: %s)", name, image.shape)
            if self._is_standalone and not self._title:
                assert isinstance(self._root, tk.Tk)
                self._title = name
                logger.debug("Setting title: '%s;", self._title)
                self._root.title(self._title)
            self._image.set_source_image(name, image)
            self._update_image(center_image=not self._initialized)

        self._root.after(1000, self._display_preview)

        if not self._initialized and self._is_standalone:
            self._initialize_window()
            self._root.mainloop()
        if not self._initialized:  # Set initialized to True for GUI
            self._set_min_max_scales()
            self._taskbar.scale_var.set("Fit")
            self._initialized = True