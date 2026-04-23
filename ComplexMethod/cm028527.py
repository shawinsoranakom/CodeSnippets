def main(_) -> None:
  # Check if the input and output directories are valid.
  if (
      not INPUT_DIRECTORY.value
      or not OUTPUT_DIRECTORY.value
      or not INPUT_DIRECTORY.value.startswith("gs://")
      or not OUTPUT_DIRECTORY.value.startswith("gs://")
  ):
    raise ValueError("Bucket path must be non-empty starting with 'gs://'")

  input_directory, prediction_folder, logger = (
      utils.setup_logger_and_directories(input_dir=INPUT_DIRECTORY.value)
  )
  filepaths_to_capture_time_dict = {
      filepath: utils.get_image_capture_time(filepath)
      for filepath in utils.files_paths(os.path.basename(input_directory))
  }

  model_manager = TritonObjectDetector(model_name=MODEL_NAME.value)
  tracking_manager = ObjectTracker(
      search_range=(SEARCH_RANGE_Y.value, SEARCH_RANGE_X.value),
      memory=MEMORY.value,
  )
  storage_manager = BigQueryManager(
      project_id=PROJECT_ID.value,
      dataset_id=BQ_DATASET_ID.value,
      table_id=BQ_TABLE_ID.value,
  )

  results = {}
  tracking_df = pd.DataFrame()
  for frame, (image_path, creation_time) in enumerate(
      filepaths_to_capture_time_dict.items(), start=1
  ):

    logger.info(f"Processing {os.path.basename(image_path)}")

    # Perform Inference
    try:
      results = model_manager.predict(
          image_path=image_path,
          confidence_threshold=PREDICTION_THRESHOLD.value,
          max_boxes=100,
          output_dims=(_IMAGE_SAVING_WIDTH, _IMAGE_SAVING_HEIGHT),
      )
      results["class_names"] = model_manager.get_class_names(results)
      logger.info(
          f"Successfully got prediction for {os.path.basename(image_path)},"
          f" with total predictions: {len(results['labels'])}"
      )
    except (KeyError, TypeError, RuntimeError, ValueError) as e:
      logger.info(
          f"Failed to get prediction for {os.path.basename(image_path)}, due to"
          f" error : {e}"
      )

    # Continue to next image if no objects detected
    if results["class_names"].size == 0:
      logger.info(f"No objects detected in {os.path.basename(image_path)}")
      continue

    # Image resizing for tracking and saving
    original_image = cv2.imread(image_path)
    image_for_tracking = cv2.resize(
        original_image,
        (_TRACKING_IMAGE_WIDTH, _TRACKING_IMAGE_HEIGHT),
        interpolation=cv2.INTER_AREA,
    )
    image_for_saving = cv2.resize(
        original_image,
        (_IMAGE_SAVING_WIDTH, _IMAGE_SAVING_HEIGHT),
        interpolation=cv2.INTER_AREA,
    )

    # Save the image with bounding boxes & masks
    try:
      pil_image = Image.fromarray(image_for_saving)
      save_path = os.path.join(
          prediction_folder, os.path.basename(image_path)
      )
      utils.draw_detections_and_save_image(pil_image, results, save_path)
      logger.info("Image with bounding box saved")
    except (KeyError, IndexError, TypeError, ValueError) as e:
      logger.info(
          f"Issue in saving visualization of results, due to error : {e}"
      )

    # Feature Extraction
    try:
      detected_colors = utils.extract_color_names(results, image_for_saving)
      tracking_manager.extract_features_for_tracking(
          image=image_for_tracking,
          results=results,
          tracking_image_size=(_TRACKING_IMAGE_WIDTH, _TRACKING_IMAGE_HEIGHT),
          image_path=image_path,
          creation_time=creation_time,
          frame_idx=frame,
          colors=detected_colors,
      )

      logger.info("Features extracted.\n")
    except (KeyError, IndexError, TypeError, ValueError) as e:
      logger.info(f"Failed to extract properties, due to error : {e}")

  # Object Tracking
  try:
    particle_df = tracking_manager.run_tracking()
    tracking_df = tracking_manager.process_tracking_results(particle_df)
    counts = tracking_df.groupby("detected_classes_names").size()
    counts.to_frame().to_csv(os.path.join(os.getcwd(), "count.csv"))
    logger.info("Object tracking applied.")
  except (KeyError, IndexError, TypeError, ValueError) as e:
    logger.info(f"Failed to apply object tracking, due to error : {e}")

  # Upload Results to BigQuery
  if isinstance(tracking_df, pd.DataFrame) and not tracking_df.empty:
    try:
      storage_manager.create_table(overwrite=OVERWRITE.value)
      storage_manager.ingest_data(tracking_df)
      storage_manager.upload_image_results_to_storage_bucket(
          input_directory=input_directory,
          prediction_folder=prediction_folder,
          output_directory=OUTPUT_DIRECTORY.value,
      )
    except (KeyError, IndexError, TypeError, ValueError) as e:
      logger.info(f"Issue in creation of table, due to error : {e}")
      return
  else:
    logger.info("No features to ingest.")
  utils.shutdown_vm()