def coco_evaluate(
        self,
        stats: dict[str, Any],
        pred_json: str,
        anno_json: str,
        iou_types: str | list[str] = "bbox",
        suffix: str | list[str] = "Box",
    ) -> dict[str, Any]:
        """Evaluate COCO/LVIS metrics using faster-coco-eval library.

        Performs evaluation using the faster-coco-eval library to compute mAP metrics for object detection. Updates the
        provided stats dictionary with computed metrics including mAP50, mAP50-95, and LVIS-specific metrics if
        applicable.

        Args:
            stats (dict[str, Any]): Dictionary to store computed metrics and statistics.
            pred_json (str | Path): Path to JSON file containing predictions in COCO format.
            anno_json (str | Path): Path to JSON file containing ground truth annotations in COCO format.
            iou_types (str | list[str]): IoU type(s) for evaluation. Can be single string or list of strings. Common
                values include "bbox", "segm", "keypoints". Defaults to "bbox".
            suffix (str | list[str]): Suffix to append to metric names in stats dictionary. Should correspond to
                iou_types if multiple types provided. Defaults to "Box".

        Returns:
            (dict[str, Any]): Updated stats dictionary containing the computed COCO/LVIS evaluation metrics.
        """
        if self.args.save_json and (self.is_coco or self.is_lvis) and len(self.jdict):
            LOGGER.info(f"\nEvaluating faster-coco-eval mAP using {pred_json} and {anno_json}...")
            try:
                for x in pred_json, anno_json:
                    assert x.is_file(), f"{x} file not found"
                iou_types = [iou_types] if isinstance(iou_types, str) else iou_types
                suffix = [suffix] if isinstance(suffix, str) else suffix
                check_requirements("faster-coco-eval>=1.6.7")
                from faster_coco_eval import COCO, COCOeval_faster

                anno = COCO(anno_json)
                pred = anno.loadRes(pred_json)
                for i, iou_type in enumerate(iou_types):
                    val = COCOeval_faster(
                        anno, pred, iouType=iou_type, lvis_style=self.is_lvis, print_function=LOGGER.info
                    )
                    val.params.imgIds = [int(Path(x).stem) for x in self.dataloader.dataset.im_files]  # images to eval
                    val.evaluate()
                    val.accumulate()
                    val.summarize()

                    # update mAP50-95 and mAP50
                    stats[f"metrics/mAP50({suffix[i][0]})"] = val.stats_as_dict["AP_50"]
                    stats[f"metrics/mAP50-95({suffix[i][0]})"] = val.stats_as_dict["AP_all"]
                    # record mAP for small, medium, large objects as well
                    stats["metrics/mAP_small(B)"] = val.stats_as_dict["AP_small"]
                    stats["metrics/mAP_medium(B)"] = val.stats_as_dict["AP_medium"]
                    stats["metrics/mAP_large(B)"] = val.stats_as_dict["AP_large"]
                    # update fitness
                    stats["fitness"] = 0.9 * val.stats_as_dict["AP_all"] + 0.1 * val.stats_as_dict["AP_50"]

                    if self.is_lvis:
                        stats[f"metrics/APr({suffix[i][0]})"] = val.stats_as_dict["APr"]
                        stats[f"metrics/APc({suffix[i][0]})"] = val.stats_as_dict["APc"]
                        stats[f"metrics/APf({suffix[i][0]})"] = val.stats_as_dict["APf"]

                if self.is_lvis:
                    stats["fitness"] = stats["metrics/mAP50-95(B)"]  # always use box mAP50-95 for fitness
            except Exception as e:
                LOGGER.warning(f"faster-coco-eval unable to run: {e}")
        return stats