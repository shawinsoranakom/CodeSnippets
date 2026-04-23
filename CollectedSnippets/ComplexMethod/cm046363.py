def plot_matches(self, img: torch.Tensor, im_file: str, save_dir: Path) -> None:
        """Plot grid of GT, TP, FP, FN for each image.

        Args:
            img (torch.Tensor): Image to plot onto.
            im_file (str): Image filename to save visualizations.
            save_dir (Path): Location to save the visualizations to.
        """
        if not self.matches:
            return
        from .ops import xyxy2xywh
        from .plotting import plot_images

        # Create batch of 4 (GT, TP, FP, FN)
        labels = defaultdict(list)
        for i, mtype in enumerate(["GT", "FP", "TP", "FN"]):
            mbatch = self.matches[mtype]
            if "conf" not in mbatch:
                mbatch["conf"] = torch.tensor([1.0] * len(mbatch["bboxes"]), device=img.device)
            mbatch["batch_idx"] = torch.ones(len(mbatch["bboxes"]), device=img.device) * i
            for k in mbatch.keys():
                labels[k] += mbatch[k]

        labels = {k: torch.stack(v, 0) if len(v) else torch.empty(0) for k, v in labels.items()}
        if self.task != "obb" and labels["bboxes"].shape[0]:
            labels["bboxes"] = xyxy2xywh(labels["bboxes"])
        (save_dir / "visualizations").mkdir(parents=True, exist_ok=True)
        plot_images(
            labels,
            img.repeat(4, 1, 1, 1),
            paths=["Ground Truth", "False Positives", "True Positives", "False Negatives"],
            fname=save_dir / "visualizations" / Path(im_file).name,
            names=self.names,
            max_subplots=4,
            conf_thres=0.001,
        )