def on_train_end(self, last, best, epoch, results):
        """Callback that runs at the end of training to save plots and log results."""
        if self.plots:
            plot_results(file=self.save_dir / "results.csv")  # save results.png
        files = ["results.png", "confusion_matrix.png", *(f"{x}_curve.png" for x in ("F1", "PR", "P", "R"))]
        files = [(self.save_dir / f) for f in files if (self.save_dir / f).exists()]  # filter
        self.logger.info(f"Results saved to {colorstr('bold', self.save_dir)}")

        if self.tb and not self.clearml:  # These images are already captured by ClearML by now, we don't want doubles
            for f in files:
                self.tb.add_image(f.stem, cv2.imread(str(f))[..., ::-1], epoch, dataformats="HWC")

        if self.wandb:
            self.wandb.log(dict(zip(self.keys[3:10], results)))
            self.wandb.log({"Results": [wandb.Image(str(f), caption=f.name) for f in files]})
            # Calling wandb.log. TODO: Refactor this into WandbLogger.log_model
            if not self.opt.evolve:
                wandb.log_artifact(
                    str(best if best.exists() else last),
                    type="model",
                    name=f"run_{self.wandb.wandb_run.id}_model",
                    aliases=["latest", "best", "stripped"],
                )
            self.wandb.finish_run()

        if self.clearml and not self.opt.evolve:
            self.clearml.log_summary(dict(zip(self.keys[3:10], results)))
            [self.clearml.log_plot(title=f.stem, plot_path=f) for f in files]
            self.clearml.log_model(
                str(best if best.exists() else last), "Best Model" if best.exists() else "Last Model", epoch
            )

        if self.comet_logger:
            final_results = dict(zip(self.keys[3:10], results))
            self.comet_logger.on_train_end(files, self.save_dir, last, best, epoch, final_results)