def _train_epoch(self, epoch):
        self.model.train()
        total_samples = 0
        train_reader_cost = 0.0
        train_batch_cost = 0.0
        reader_start = time.time()
        epoch_start = time.time()
        train_loss = 0.0
        running_metric_text = runningScore(2)

        for i, batch in enumerate(self.train_loader):
            profiler.add_profiler_step(self.profiler_options)
            if i >= self.train_loader_len:
                break
            self.global_step += 1
            lr = self.optimizer.get_lr()

            cur_batch_size = batch["img"].shape[0]

            train_reader_cost += time.time() - reader_start
            if self.amp:
                with paddle.amp.auto_cast(
                    enable="gpu" in paddle.device.get_device(),
                    custom_white_list=self.amp.get("custom_white_list", []),
                    custom_black_list=self.amp.get("custom_black_list", []),
                    level=self.amp.get("level", "O2"),
                ):
                    preds = self.model(batch["img"])
                loss_dict = self.criterion(preds.astype(paddle.float32), batch)
                scaled_loss = self.amp["scaler"].scale(loss_dict["loss"])
                scaled_loss.backward()
                self.amp["scaler"].minimize(self.optimizer, scaled_loss)
            else:
                preds = self.model(batch["img"])
                loss_dict = self.criterion(preds, batch)
                # backward
                loss_dict["loss"].backward()
                self.optimizer.step()
            self.lr_scheduler.step()
            self.optimizer.clear_grad()

            train_batch_time = time.time() - reader_start
            train_batch_cost += train_batch_time
            total_samples += cur_batch_size

            # acc iou
            score_shrink_map = cal_text_score(
                preds[:, 0, :, :],
                batch["shrink_map"],
                batch["shrink_mask"],
                running_metric_text,
                thred=self.config["post_processing"]["args"]["thresh"],
            )

            # loss 和 acc 记录到日志
            loss_str = "loss: {:.4f}, ".format(loss_dict["loss"].item())
            for idx, (key, value) in enumerate(loss_dict.items()):
                loss_dict[key] = value.item()
                if key == "loss":
                    continue
                loss_str += "{}: {:.4f}".format(key, loss_dict[key])
                if idx < len(loss_dict) - 1:
                    loss_str += ", "

            train_loss += loss_dict["loss"]
            acc = score_shrink_map["Mean Acc"]
            iou_shrink_map = score_shrink_map["Mean IoU"]

            if self.global_step % self.log_iter == 0:
                self.logger_info(
                    "[{}/{}], [{}/{}], global_step: {}, ips: {:.1f} samples/sec, avg_reader_cost: {:.5f} s, avg_batch_cost: {:.5f} s, avg_samples: {}, acc: {:.4f}, iou_shrink_map: {:.4f}, {}lr:{:.6}, time:{:.2f}".format(
                        epoch,
                        self.epochs,
                        i + 1,
                        self.train_loader_len,
                        self.global_step,
                        total_samples / train_batch_cost,
                        train_reader_cost / self.log_iter,
                        train_batch_cost / self.log_iter,
                        total_samples / self.log_iter,
                        acc,
                        iou_shrink_map,
                        loss_str,
                        lr,
                        train_batch_cost,
                    )
                )
                total_samples = 0
                train_reader_cost = 0.0
                train_batch_cost = 0.0

            if self.visualdl_enable and paddle.distributed.get_rank() == 0:
                # write tensorboard
                for key, value in loss_dict.items():
                    self.writer.add_scalar(
                        "TRAIN/LOSS/{}".format(key), value, self.global_step
                    )
                self.writer.add_scalar("TRAIN/ACC_IOU/acc", acc, self.global_step)
                self.writer.add_scalar(
                    "TRAIN/ACC_IOU/iou_shrink_map", iou_shrink_map, self.global_step
                )
                self.writer.add_scalar("TRAIN/lr", lr, self.global_step)
            reader_start = time.time()
        return {
            "train_loss": train_loss / self.train_loader_len,
            "lr": lr,
            "time": time.time() - epoch_start,
            "epoch": epoch,
        }