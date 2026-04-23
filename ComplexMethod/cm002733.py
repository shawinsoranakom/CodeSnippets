def LwDetrForObjectDetectionLoss(
    logits,
    labels,
    device,
    pred_boxes,
    config,
    outputs_class=None,
    outputs_coord=None,
    enc_outputs_class=None,
    enc_outputs_coord=None,
    **kwargs,
):
    # First: create the matcher
    matcher = LwDetrHungarianMatcher(
        class_cost=config.class_cost, bbox_cost=config.bbox_cost, giou_cost=config.giou_cost
    )
    # Second: create the criterion
    losses = ["labels", "boxes", "cardinality"]
    criterion = LwDetrImageLoss(
        matcher=matcher,
        num_classes=config.num_labels,
        focal_alpha=config.focal_alpha,
        losses=losses,
        group_detr=config.group_detr,
    )
    criterion.to(device)
    # Third: compute the losses, based on outputs and labels
    outputs_loss = {}
    auxiliary_outputs = None
    outputs_loss["logits"] = logits
    outputs_loss["pred_boxes"] = pred_boxes
    outputs_loss["enc_outputs"] = {
        "logits": enc_outputs_class,
        "pred_boxes": enc_outputs_coord,
    }
    if config.auxiliary_loss:
        auxiliary_outputs = _set_aux_loss(outputs_class, outputs_coord)
        outputs_loss["auxiliary_outputs"] = auxiliary_outputs
    loss_dict = criterion(outputs_loss, labels)
    # Fourth: compute total loss, as a weighted sum of the various losses
    weight_dict = {"loss_ce": 1, "loss_bbox": config.bbox_loss_coefficient}
    weight_dict["loss_giou"] = config.giou_loss_coefficient
    if config.auxiliary_loss:
        aux_weight_dict = {}
        for i in range(config.decoder_layers - 1):
            aux_weight_dict.update({k + f"_{i}": v for k, v in weight_dict.items()})
        weight_dict.update(aux_weight_dict)
    enc_weight_dict = {k + "_enc": v for k, v in weight_dict.items()}
    weight_dict.update(enc_weight_dict)
    loss = sum(loss_dict[k] * weight_dict[k] for k in loss_dict if k in weight_dict)
    return loss, loss_dict, auxiliary_outputs