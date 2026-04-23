def log_images(self, files, name="Images", epoch=0):
        """Logs images to all loggers with optional naming and epoch specification."""
        files = [Path(f) for f in (files if isinstance(files, (tuple, list)) else [files])]  # to Path
        files = [f for f in files if f.exists()]  # filter by exists

        if self.tb:
            for f in files:
                self.tb.add_image(f.stem, cv2.imread(str(f))[..., ::-1], epoch, dataformats="HWC")

        if self.wandb:
            self.wandb.log({name: [wandb.Image(str(f), caption=f.name) for f in files]}, step=epoch)

        if self.clearml:
            if name == "Results":
                [self.clearml.log_plot(f.stem, f) for f in files]
            else:
                self.clearml.log_debug_samples(files, title=name)