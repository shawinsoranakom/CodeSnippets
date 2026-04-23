def plot_images(
    labels: dict[str, Any],
    images: torch.Tensor | np.ndarray = np.zeros((0, 3, 640, 640), dtype=np.float32),
    paths: list[str] | None = None,
    fname: str = "images.jpg",
    names: dict[int, str] | None = None,
    on_plot: Callable | None = None,
    max_size: int = 1920,
    max_subplots: int = 16,
    save: bool = True,
    conf_thres: float = 0.25,
) -> np.ndarray | None:
    """Plot image grid with labels, bounding boxes, masks, and keypoints.

    Args:
        labels (dict[str, Any]): Dictionary containing detection data with keys like 'cls', 'bboxes', 'conf', 'masks',
            'keypoints', 'batch_idx', 'img'.
        images (torch.Tensor | np.ndarray): Batch of images to plot. Shape: (batch_size, channels, height, width).
        paths (list[str] | None): List of file paths for each image in the batch.
        fname (str): Output filename for the plotted image grid.
        names (dict[int, str] | None): Dictionary mapping class indices to class names.
        on_plot (Callable | None): Callback function to be called after saving the plot.
        max_size (int): Maximum size of the output image grid.
        max_subplots (int): Maximum number of subplots in the image grid.
        save (bool): Whether to save the plotted image grid to a file.
        conf_thres (float): Confidence threshold for displaying detections.

    Returns:
        (np.ndarray | None): Plotted image grid as a numpy array if save is False, None otherwise.

    Notes:
        This function supports both tensor and numpy array inputs. It will automatically
        convert tensor inputs to numpy arrays for processing.

        Channel Support:
        - 1 channel: Grayscale
        - 2 channels: Third channel added as zeros
        - 3 channels: Used as-is (standard RGB)
        - 4+ channels: Cropped to first 3 channels
    """
    for k in {"cls", "bboxes", "conf", "masks", "keypoints", "batch_idx", "images"}:
        if k not in labels:
            continue
        if k == "cls" and labels[k].ndim == 2:
            labels[k] = labels[k].squeeze(1)  # squeeze if shape is (n, 1)
        if isinstance(labels[k], torch.Tensor):
            labels[k] = labels[k].cpu().numpy()

    cls = labels.get("cls", np.zeros(0, dtype=np.int64))
    batch_idx = labels.get("batch_idx", np.zeros(cls.shape, dtype=np.int64))
    bboxes = labels.get("bboxes", np.zeros(0, dtype=np.float32))
    confs = labels.get("conf", None)
    masks = labels.get("masks", np.zeros(0, dtype=np.uint8))
    kpts = labels.get("keypoints", np.zeros(0, dtype=np.float32))
    images = labels.get("img", images)  # default to input images

    if len(images) and isinstance(images, torch.Tensor):
        images = images.cpu().float().numpy()

    # Handle 2-ch and n-ch images
    c = images.shape[1]
    if c == 2:
        zero = np.zeros_like(images[:, :1])
        images = np.concatenate((images, zero), axis=1)  # pad 2-ch with a black channel
    elif c > 3:
        images = images[:, :3]  # crop multispectral images to first 3 channels

    bs, _, h, w = images.shape  # batch size, _, height, width
    bs = min(bs, max_subplots)  # limit plot images
    ns = np.ceil(bs**0.5)  # number of subplots (square)
    if np.max(images[0]) <= 1:
        images *= 255  # de-normalise (optional)

    # Build Image
    mosaic = np.full((int(ns * h), int(ns * w), 3), 255, dtype=np.uint8)  # init
    for i in range(bs):
        x, y = int(w * (i // ns)), int(h * (i % ns))  # block origin
        mosaic[y : y + h, x : x + w, :] = images[i].transpose(1, 2, 0)

    # Resize (optional)
    scale = max_size / ns / max(h, w)
    if scale < 1:
        h = math.ceil(scale * h)
        w = math.ceil(scale * w)
        mosaic = cv2.resize(mosaic, tuple(int(x * ns) for x in (w, h)))

    # Annotate
    fs = int((h + w) * ns * 0.01)  # font size
    fs = max(fs, 18)  # ensure that the font size is large enough to be easily readable.
    annotator = Annotator(mosaic, line_width=round(fs / 10), font_size=fs, pil=True, example=str(names))
    for i in range(bs):
        x, y = int(w * (i // ns)), int(h * (i % ns))  # block origin
        annotator.rectangle([x, y, x + w, y + h], None, (255, 255, 255), width=2)  # borders
        if paths:
            annotator.text([x + 5, y + 5], text=Path(paths[i]).name[:40], txt_color=(220, 220, 220))  # filenames
        if len(cls) > 0:
            idx = batch_idx == i
            classes = cls[idx].astype("int")
            labels = confs is None
            conf = confs[idx] if confs is not None else None  # check for confidence presence (label vs pred)

            if len(bboxes):
                boxes = bboxes[idx]
                if len(boxes):
                    if boxes[:, :4].max() <= 1.1:  # if normalized with tolerance 0.1
                        boxes[..., [0, 2]] *= w  # scale to pixels
                        boxes[..., [1, 3]] *= h
                    elif scale < 1:  # absolute coords need scale if image scales
                        boxes[..., :4] *= scale
                boxes[..., 0] += x
                boxes[..., 1] += y
                is_obb = boxes.shape[-1] == 5  # xywhr
                boxes = ops.xywhr2xyxyxyxy(boxes) if is_obb else ops.xywh2xyxy(boxes)
                for j, box in enumerate(boxes.astype(np.int64).tolist()):
                    c = classes[j]
                    color = colors(c)
                    c = names.get(c, c) if names else c
                    if labels or conf[j] > conf_thres:
                        label = f"{c}" if labels else f"{c} {conf[j]:.1f}"
                        annotator.box_label(box, label, color=color)

            elif len(classes):
                for c in classes:
                    color = colors(c)
                    c = names.get(c, c) if names else c
                    label = f"{c}" if labels else f"{c} {conf[0]:.1f}"
                    annotator.text([x, y], label, txt_color=color, box_color=(64, 64, 64, 128))

            # Plot keypoints
            if len(kpts):
                kpts_ = kpts[idx].copy()
                if len(kpts_):
                    if kpts_[..., 0].max() <= 1.01 or kpts_[..., 1].max() <= 1.01:  # if normalized with tolerance .01
                        kpts_[..., 0] *= w  # scale to pixels
                        kpts_[..., 1] *= h
                    elif scale < 1:  # absolute coords need scale if image scales
                        kpts_ *= scale
                kpts_[..., 0] += x
                kpts_[..., 1] += y
                for j in range(len(kpts_)):
                    if labels or conf[j] > conf_thres:
                        annotator.kpts(kpts_[j], conf_thres=conf_thres)

            # Plot masks
            if len(masks):
                if idx.shape[0] == masks.shape[0] and masks.max() <= 1:  # overlap_mask=False
                    image_masks = masks[idx]
                else:  # overlap_mask=True
                    image_masks = masks[[i]]  # (1, 640, 640)
                    nl = idx.sum()
                    index = np.arange(1, nl + 1).reshape((nl, 1, 1))
                    image_masks = (image_masks == index).astype(np.float32)

                im = np.asarray(annotator.im).copy()
                for j in range(len(image_masks)):
                    if labels or conf[j] > conf_thres:
                        color = colors(classes[j])
                        mh, mw = image_masks[j].shape
                        if mh != h or mw != w:
                            mask = image_masks[j].astype(np.uint8)
                            mask = cv2.resize(mask, (w, h))
                            mask = mask.astype(bool)
                        else:
                            mask = image_masks[j].astype(bool)
                        try:
                            im[y : y + h, x : x + w, :][mask] = (
                                im[y : y + h, x : x + w, :][mask] * 0.4 + np.array(color) * 0.6
                            )
                        except Exception:
                            pass
                annotator.fromarray(im)
    if not save:
        return np.asarray(annotator.im)
    annotator.im.save(fname)  # save
    if on_plot:
        on_plot(fname)