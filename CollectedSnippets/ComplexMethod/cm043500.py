def on_fit_epoch_end(self, vals, epoch, best_fitness, fi):
        """Callback that logs metrics and saves them to CSV or NDJSON at the end of each fit (train+val) epoch."""
        x = dict(zip(self.keys, vals))
        if self.csv:
            file = self.save_dir / "results.csv"
            n = len(x) + 1  # number of cols
            s = "" if file.exists() else (("%20s," * n % tuple(["epoch", *self.keys])).rstrip(",") + "\n")  # add header
            with open(file, "a") as f:
                f.write(s + ("%20.5g," * n % tuple([epoch, *vals])).rstrip(",") + "\n")
        if self.ndjson_console or self.ndjson_file:
            json_data = json.dumps(dict(epoch=epoch, **x), default=_json_default)
        if self.ndjson_console:
            print(json_data)
        if self.ndjson_file:
            file = self.save_dir / "results.ndjson"
            with open(file, "a") as f:
                print(json_data, file=f)

        if self.tb:
            for k, v in x.items():
                self.tb.add_scalar(k, v, epoch)
        elif self.clearml:  # log to ClearML if TensorBoard not used
            self.clearml.log_scalars(x, epoch)

        if self.wandb:
            if best_fitness == fi:
                best_results = [epoch, *vals[3:7]]
                for i, name in enumerate(self.best_keys):
                    self.wandb.wandb_run.summary[name] = best_results[i]  # log best results in the summary
            self.wandb.log(x)
            self.wandb.end_epoch()

        if self.clearml:
            self.clearml.current_epoch_logged_images = set()  # reset epoch image limit
            self.clearml.current_epoch += 1

        if self.comet_logger:
            self.comet_logger.on_fit_epoch_end(x, epoch=epoch)