def _on_epoch_finish(self):
        self.logger_info(
            "[{}/{}], train_loss: {:.4f}, time: {:.4f}, lr: {}".format(
                self.epoch_result["epoch"],
                self.epochs,
                self.epoch_result["train_loss"],
                self.epoch_result["time"],
                self.epoch_result["lr"],
            )
        )
        net_save_path = "{}/model_latest.pth".format(self.checkpoint_dir)
        net_save_path_best = "{}/model_best.pth".format(self.checkpoint_dir)

        if paddle.distributed.get_rank() == 0:
            self._save_checkpoint(self.epoch_result["epoch"], net_save_path)
            save_best = False
            if (
                self.validate_loader is not None
                and self.metric_cls is not None
                and self.enable_eval
            ):  # 使用f1作为最优模型指标
                recall, precision, hmean = self._eval(self.epoch_result["epoch"])

                if self.visualdl_enable:
                    self.writer.add_scalar("EVAL/recall", recall, self.global_step)
                    self.writer.add_scalar(
                        "EVAL/precision", precision, self.global_step
                    )
                    self.writer.add_scalar("EVAL/hmean", hmean, self.global_step)
                self.logger_info(
                    "test: recall: {:.6f}, precision: {:.6f}, hmean: {:.6f}".format(
                        recall, precision, hmean
                    )
                )

                if hmean >= self.metrics["hmean"]:
                    save_best = True
                    self.metrics["train_loss"] = self.epoch_result["train_loss"]
                    self.metrics["hmean"] = hmean
                    self.metrics["precision"] = precision
                    self.metrics["recall"] = recall
                    self.metrics["best_model_epoch"] = self.epoch_result["epoch"]
            else:
                if self.epoch_result["train_loss"] <= self.metrics["train_loss"]:
                    save_best = True
                    self.metrics["train_loss"] = self.epoch_result["train_loss"]
                    self.metrics["best_model_epoch"] = self.epoch_result["epoch"]
            best_str = "current best, "
            for k, v in self.metrics.items():
                best_str += "{}: {:.6f}, ".format(k, v)
            self.logger_info(best_str)
            if save_best:
                import shutil

                shutil.copy(net_save_path, net_save_path_best)
                self.logger_info("Saving current best: {}".format(net_save_path_best))
            else:
                self.logger_info("Saving checkpoint: {}".format(net_save_path))