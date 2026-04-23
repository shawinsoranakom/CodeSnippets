def convert_segment_masks_to_yolo_seg(masks_dir: str, output_dir: str, classes: int):
    """Convert a dataset of segmentation mask images to the YOLO segmentation format.

    This function takes the directory containing the binary format mask images and converts them into YOLO segmentation
    format. The converted masks are saved in the specified output directory.

    Args:
        masks_dir (str): The path to the directory where all mask images (png, jpg) are stored.
        output_dir (str): The path to the directory where the converted YOLO segmentation masks will be stored.
        classes (int): Total number of classes in the dataset, e.g., 80 for COCO.

    Examples:
        >>> from ultralytics.data.converter import convert_segment_masks_to_yolo_seg

        The classes here is the total classes in the dataset, for COCO dataset we have 80 classes
        >>> convert_segment_masks_to_yolo_seg("path/to/masks_directory", "path/to/output/directory", classes=80)

    Notes:
        The expected directory structure for the masks is:

            - masks
                ├─ mask_image_01.png or mask_image_01.jpg
                ├─ mask_image_02.png or mask_image_02.jpg
                ├─ mask_image_03.png or mask_image_03.jpg
                └─ mask_image_04.png or mask_image_04.jpg

        After execution, the labels will be organized in the following structure:

            - output_dir
                ├─ mask_yolo_01.txt
                ├─ mask_yolo_02.txt
                ├─ mask_yolo_03.txt
                └─ mask_yolo_04.txt
    """
    pixel_to_class_mapping = {i + 1: i for i in range(classes)}
    for mask_path in Path(masks_dir).iterdir():
        if mask_path.suffix in {".png", ".jpg"}:
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)  # Read the mask image in grayscale
            img_height, img_width = mask.shape  # Get image dimensions
            LOGGER.info(f"Processing {mask_path} imgsz = {img_height} x {img_width}")

            unique_values = np.unique(mask)  # Get unique pixel values representing different classes
            yolo_format_data = []

            for value in unique_values:
                if value == 0:
                    continue  # Skip background
                class_index = pixel_to_class_mapping.get(value, -1)
                if class_index == -1:
                    LOGGER.warning(f"Unknown class for pixel value {value} in file {mask_path}, skipping.")
                    continue

                # Create a binary mask for the current class and find contours
                contours, _ = cv2.findContours(
                    (mask == value).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )  # Find contours

                for contour in contours:
                    if len(contour) >= 3:  # YOLO requires at least 3 points for a valid segmentation
                        contour = contour.squeeze()  # Remove single-dimensional entries
                        yolo_format = [class_index]
                        for point in contour:
                            # Normalize the coordinates
                            yolo_format.append(round(point[0] / img_width, 6))  # Rounding to 6 decimal places
                            yolo_format.append(round(point[1] / img_height, 6))
                        yolo_format_data.append(yolo_format)
            # Save Ultralytics YOLO format data to file
            output_path = Path(output_dir) / f"{mask_path.stem}.txt"
            with open(output_path, "w", encoding="utf-8") as file:
                for item in yolo_format_data:
                    line = " ".join(map(str, item))
                    file.write(line + "\n")
            LOGGER.info(f"Processed and stored at {output_path} imgsz = {img_height} x {img_width}")