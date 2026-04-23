def GroundingDinoForObjectDetectionLoss(
    logits,
    labels,
    device,
    pred_boxes,
    config,
    label_maps,
    text_mask,
    outputs_class=None,
    outputs_coord=None,
    encoder_logits=None,
    encoder_pred_boxes=None,
):
    # First: create the matcher
    matcher = GroundingDinoHungarianMatcher(
        class_cost=config.class_cost, bbox_cost=config.bbox_cost, giou_cost=config.giou_cost
    )
    # Second: create the criterion
    losses = ["labels", "boxes", "cardinality"]
    criterion = GroundingDinoImageLoss(
        matcher=matcher,
        focal_alpha=config.focal_alpha,
        losses=losses,
    )
    criterion.to(device)
    # Third: compute the losses, based on outputs and labels
    outputs_loss = {}
    outputs_loss["logits"] = logits
    outputs_loss["pred_boxes"] = pred_boxes
    outputs_loss["label_maps"] = label_maps
    outputs_loss["text_mask"] = text_mask

    auxiliary_outputs = None
    if config.auxiliary_loss:
        auxiliary_outputs = _set_aux_loss(outputs_class, outputs_coord)
        for aux_output in auxiliary_outputs:
            aux_output["label_maps"] = label_maps
            aux_output["text_mask"] = text_mask
        outputs_loss["auxiliary_outputs"] = auxiliary_outputs

    loss_dict = criterion(outputs_loss, labels)

    if config.two_stage:
        encoder_outputs_loss = {
            "logits": encoder_logits,
            "pred_boxes": encoder_pred_boxes,
            "label_maps": label_maps,
            "text_mask": text_mask,
        }
        encoder_loss_dict = criterion(encoder_outputs_loss, labels)
        encoder_loss_dict = {k + "_enc": v for k, v in encoder_loss_dict.items()}
        loss_dict.update(encoder_loss_dict)
    # Fourth: compute total loss, as a weighted sum of the various losses
    weight_dict = {
        "loss_ce": 2.0,
        "loss_bbox": config.bbox_loss_coefficient,
        "loss_giou": config.giou_loss_coefficient,
    }

    if config.two_stage:
        enc_weight_dict = {k + "_enc": v for k, v in weight_dict.items()}
        weight_dict.update(enc_weight_dict)

    if config.auxiliary_loss:
        aux_weight_dict = {}
        for i in range(config.decoder_layers - 1):
            aux_weight_dict.update({k + f"_{i}": v for k, v in weight_dict.items()})
        weight_dict.update(aux_weight_dict)

    loss = sum(loss_dict[k] * weight_dict[k] for k in loss_dict if k in weight_dict)
    return loss, loss_dict, auxiliary_outputs