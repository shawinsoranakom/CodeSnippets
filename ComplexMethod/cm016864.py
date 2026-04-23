def execute(cls, folder):
        logging.info(f"Loading images from folder: {folder}")

        sub_input_dir = os.path.join(folder_paths.get_input_directory(), folder)
        valid_extensions = [".png", ".jpg", ".jpeg", ".webp"]

        image_files = []
        for item in os.listdir(sub_input_dir):
            path = os.path.join(sub_input_dir, item)
            if any(item.lower().endswith(ext) for ext in valid_extensions):
                image_files.append(path)
            elif os.path.isdir(path):
                # Support kohya-ss/sd-scripts folder structure
                repeat = 1
                if item.split("_")[0].isdigit():
                    repeat = int(item.split("_")[0])
                image_files.extend(
                    [
                        os.path.join(path, f)
                        for f in os.listdir(path)
                        if any(f.lower().endswith(ext) for ext in valid_extensions)
                    ]
                    * repeat
                )

        caption_file_path = [
            f.replace(os.path.splitext(f)[1], ".txt") for f in image_files
        ]
        captions = []
        for caption_file in caption_file_path:
            caption_path = os.path.join(sub_input_dir, caption_file)
            if os.path.exists(caption_path):
                with open(caption_path, "r", encoding="utf-8") as f:
                    caption = f.read().strip()
                    captions.append(caption)
            else:
                captions.append("")

        output_tensor = load_and_process_images(image_files, sub_input_dir)

        logging.info(f"Loaded {len(output_tensor)} images from {sub_input_dir}.")
        return io.NodeOutput(output_tensor, captions)