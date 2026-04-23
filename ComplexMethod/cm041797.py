def log(self, logs: dict[str, float], *args, **kwargs) -> None:
        r"""Log `logs` on the various objects watching training, including stored metrics."""
        # logs either has "loss" or "eval_loss"
        train_eval = "train" if "loss" in logs else "eval"
        prefix = "eval_" if train_eval == "eval" else ""
        # Add averaged stored metrics to logs
        key_list, metric_list = [], []
        for key, metrics in self._stored_metrics[train_eval].items():
            key_list.append(key)
            metric_list.append(torch.tensor(metrics, dtype=torch.float).to(self.accelerator.device).sum().item())

        del self._stored_metrics[train_eval]
        if len(metric_list) < 9:  # pad to for all reduce
            for i in range(9 - len(metric_list)):
                key_list.append(f"dummy_{i}")
                metric_list.append(0.0)

        metric_list = torch.tensor(metric_list, dtype=torch.float).to(self.accelerator.device)
        metric_list = self.accelerator.reduce(metric_list, "sum").tolist()
        metric_dict: dict[str, float] = dict(zip(key_list, metric_list))
        for split in ["chosen", "rejected"]:  # accumulate average metrics from sums and lengths
            if f"count/{split}" in metric_dict:
                for key in ("rewards", "logps", "logits"):
                    logs[f"{prefix}{key}/{split}"] = metric_dict[f"{key}/{split}_sum"] / metric_dict[f"count/{split}"]
                    del metric_dict[f"{key}/{split}_sum"]
                del metric_dict[f"count/{split}"]

        if f"{prefix}rewards/chosen" in logs and f"{prefix}rewards/rejected" in logs:  # calculate reward margin
            logs[f"{prefix}rewards/margins"] = logs[f"{prefix}rewards/chosen"] - logs[f"{prefix}rewards/rejected"]

        for key, metric in metric_dict.items():  # add remaining items
            if not key.startswith("dummy_"):
                logs[key] = metric

        return Trainer.log(self, logs, *args, **kwargs)