def on_train_epoch_end(self, trainer, pl_module):
        # if not self._should_skip_saving_checkpoint(trainer) and self._should_save_on_train_epoch_end(trainer):
        if self._should_save_on_train_epoch_end(trainer):
            monitor_candidates = self._monitor_candidates(trainer)
            if self._every_n_epochs >= 1 and (trainer.current_epoch + 1) % self._every_n_epochs == 0:
                if (
                    self.if_save_latest == True
                ):  ####如果设置只保存最后一个ckpt，在保存下一个ckpt后要清理掉之前的所有ckpt
                    to_clean = list(os.listdir(self.dirpath))
                self._save_topk_checkpoint(trainer, monitor_candidates)
                if self.if_save_latest == True:
                    for name in to_clean:
                        try:
                            os.remove("%s/%s" % (self.dirpath, name))
                        except:
                            pass
                if self.if_save_every_weights == True:
                    to_save_od = OrderedDict()
                    to_save_od["weight"] = OrderedDict()
                    dictt = trainer.strategy._lightning_module.state_dict()
                    for key in dictt:
                        to_save_od["weight"][key] = dictt[key].half()
                    to_save_od["config"] = self.config
                    to_save_od["info"] = "GPT-e%s" % (trainer.current_epoch + 1)
                    # torch.save(
                    # print(os.environ)
                    if os.environ.get("LOCAL_RANK", "0") == "0":
                        my_save(
                            to_save_od,
                            "%s/%s-e%s.ckpt"
                            % (
                                self.half_weights_save_dir,
                                self.exp_name,
                                trainer.current_epoch + 1,
                            ),
                        )
            self._save_last_checkpoint(trainer, monitor_candidates)