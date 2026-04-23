def save_images_to_folder(image_list, output_dir, prefix="image"):
    """Utility function to save a list of image tensors to disk.

    Args:
        image_list: List of image tensors (each [1, H, W, C] or [H, W, C] or [C, H, W])
        output_dir: Directory to save images to
        prefix: Filename prefix

    Returns:
        List of saved filenames
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    for idx, img_tensor in enumerate(image_list):
        # Handle different tensor shapes
        if isinstance(img_tensor, torch.Tensor):
            # Remove batch dimension if present [1, H, W, C] -> [H, W, C]
            if img_tensor.dim() == 4 and img_tensor.shape[0] == 1:
                img_tensor = img_tensor.squeeze(0)

            # If tensor is [C, H, W], permute to [H, W, C]
            if img_tensor.dim() == 3 and img_tensor.shape[0] in [1, 3, 4]:
                if (
                    img_tensor.shape[0] <= 4
                    and img_tensor.shape[1] > 4
                    and img_tensor.shape[2] > 4
                ):
                    img_tensor = img_tensor.permute(1, 2, 0)

            # Convert to numpy and scale to 0-255
            img_array = img_tensor.cpu().numpy()
            img_array = np.clip(img_array * 255.0, 0, 255).astype(np.uint8)

            # Convert to PIL Image
            img = Image.fromarray(img_array)
        else:
            raise ValueError(f"Expected torch.Tensor, got {type(img_tensor)}")

        # Save image
        filename = f"{prefix}_{idx:05d}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath)
        saved_files.append(filename)

    return saved_files