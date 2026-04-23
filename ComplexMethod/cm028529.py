def main(_) -> None:
  """Runs the main object detection and extraction pipeline."""
  if not os.path.isdir(INPUT_DIR):
    raise ValueError(f"Input directory not found at '{INPUT_DIR}'")

  # Check if COCO output should be created
  create_coco = FLAGS.category_name is not None

  print("Initializing image extraction and classification...")
  try:
    pipeline = detection_segmentation.ObjectDetectionSegmentation(
        dino_config_path=GROUNDING_DINO_CONFIG,
        dino_weights_path=GROUNDING_DINO_WEIGHTS,
        sam_config_path=SAM2_CONFIG,
        sam_checkpoint_path=SAM2_WEIGHTS,
    )
  except FileNotFoundError as e:
    print(
        f"\n⚠️ Error: Could not find model files: {e}. "
        "Please check the paths in the script."
    )
    return
  print("✅ Pipeline ready.")
  os.makedirs(CLASSIFICATION_DIR, exist_ok=True)

  # Initialize COCO annotation writer only if category_name is provided
  coco_writer = None
  if create_coco:
    coco_writer = coco_annotation_writer.CocoAnnotationWriter(
        FLAGS.category_name
    )
    print(
        f"COCO JSON output will be created for category: {FLAGS.category_name}"
    )
  else:
    print("No category name provided. Skipping COCO JSON creation.")

  # Get all image files.
  all_files = glob.glob(os.path.join(INPUT_DIR, "*"))
  image_extensions = (".jpg", ".jpeg", ".png", ".bmp")
  files = [f for f in all_files if f.lower().endswith(image_extensions)]
  files = natsort.natsorted(files)

  writer = batched_io.BatchedMaskWriter(CLASSIFICATION_DIR)

  try:
    for file_path in tqdm.tqdm(files):
      try:
        with torch.no_grad():
          results = pipeline.detect_and_segment(file_path, TEXT_PROMPT)
        if not results:
          print("No objects detected")
          continue
      except (RuntimeError, ValueError) as e:
        print(
            "An unexpected error occurred with"
            f" {os.path.basename(file_path)}: {e}"
        )
        continue

      image = results["image"]
      h, w = image.shape[:2]
      image_area = h * w

      valid_masks, valid_boxes = filter_masks_by_area(
          results["masks"],
          results["boxes"],
          image_area,
          min_percent=MASK_FILTER_THRESHOLD_PERCENT,
      )

      writer.add_batch(
          image,
          valid_masks,
          valid_boxes,
          file_path,
      )

      # Add image info to COCO output only if create_coco is True
      if create_coco and coco_writer:
        current_image_id = coco_writer.add_image(file_path, w, h)
        coco_writer.add_annotations(current_image_id, valid_boxes, valid_masks)

  finally:
    # Ensure all I/O operations complete
    if writer:
      writer.__exit__(None, None, None)

  # Save COCO JSON file only if create_coco is True
  if create_coco and coco_writer:
    output_path = os.path.join(INPUT_DIR, COCO_OUTPUT_PATH)
    coco_writer.save(output_path)
    stats = coco_writer.get_statistics()
    print(
        f"\n✅ COCO JSON saved to '{COCO_OUTPUT_PATH}'"
        f" ({stats['num_images']} images,"
        f" {stats['num_annotations']} annotations)."
    )

  print(f"✅ Cropped images saved to '{CLASSIFICATION_DIR}'.")