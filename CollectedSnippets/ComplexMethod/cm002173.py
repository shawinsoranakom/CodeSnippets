def evaluation_loop(model, image_processor, accelerator: Accelerator, dataloader, id2label):
    metric = MeanAveragePrecision(iou_type="segm", class_metrics=True)

    for inputs in tqdm(dataloader, total=len(dataloader), disable=not accelerator.is_local_main_process):
        with torch.no_grad():
            outputs = model(**inputs)

        inputs = accelerator.gather_for_metrics(inputs)
        inputs = nested_cpu(inputs)

        outputs = accelerator.gather_for_metrics(outputs)
        outputs = nested_cpu(outputs)

        # For metric computation we need to provide:
        #  - targets in a form of list of dictionaries with keys "masks", "labels"
        #  - predictions in a form of list of dictionaries with keys "masks", "labels", "scores"

        post_processed_targets = []
        post_processed_predictions = []
        target_sizes = []

        # Collect targets
        for masks, labels in zip(inputs["mask_labels"], inputs["class_labels"]):
            post_processed_targets.append(
                {
                    "masks": masks.to(dtype=torch.bool),
                    "labels": labels,
                }
            )
            target_sizes.append(masks.shape[-2:])

        # Collect predictions
        post_processed_output = image_processor.post_process_instance_segmentation(
            outputs,
            threshold=0.0,
            target_sizes=target_sizes,
            return_binary_maps=True,
        )

        for image_predictions, target_size in zip(post_processed_output, target_sizes):
            if image_predictions["segments_info"]:
                post_processed_image_prediction = {
                    "masks": image_predictions["segmentation"].to(dtype=torch.bool),
                    "labels": torch.tensor([x["label_id"] for x in image_predictions["segments_info"]]),
                    "scores": torch.tensor([x["score"] for x in image_predictions["segments_info"]]),
                }
            else:
                # for void predictions, we need to provide empty tensors
                post_processed_image_prediction = {
                    "masks": torch.zeros([0, *target_size], dtype=torch.bool),
                    "labels": torch.tensor([]),
                    "scores": torch.tensor([]),
                }
            post_processed_predictions.append(post_processed_image_prediction)

        # Update metric for batch targets and predictions
        metric.update(post_processed_predictions, post_processed_targets)

    # Compute metrics
    metrics = metric.compute()

    # Replace list of per class metrics with separate metric for each class
    classes = metrics.pop("classes")
    map_per_class = metrics.pop("map_per_class")
    mar_100_per_class = metrics.pop("mar_100_per_class")
    for class_id, class_map, class_mar in zip(classes, map_per_class, mar_100_per_class):
        class_name = id2label[class_id.item()] if id2label is not None else class_id.item()
        metrics[f"map_{class_name}"] = class_map
        metrics[f"mar_100_{class_name}"] = class_mar

    metrics = {k: round(v.item(), 4) for k, v in metrics.items()}

    return metrics