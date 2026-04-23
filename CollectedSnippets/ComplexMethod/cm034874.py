def optimize_image(
    input_path: Path,
    output_path: Path,
    quality: int = DEFAULT_QUALITY,
    max_size_mb: float = DEFAULT_TARGET_SIZE_MB,
) -> None:
    """Optimize image file by reducing quality and/or resolution."""
    from PIL import Image

    if input_path.stat().st_size == 0:
        raise ValueError("Input file is empty (0 bytes); nothing to optimize")

    print(f"Optimizing image: {input_path}")

    img = Image.open(input_path)
    original_size = input_path.stat().st_size / 1024 / 1024

    print(f"Original size: {original_size:.2f}MB")
    print(f"Original dimensions: {img.size[0]}x{img.size[1]}")

    is_jpeg = output_path.suffix.lower() in (".jpg", ".jpeg")

    if is_jpeg and img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(
            img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None
        )
        img = background

    save_kwargs = {"optimize": True}
    if is_jpeg or output_path.suffix.lower() == ".webp":
        save_kwargs["quality"] = quality

    def _save(image):
        image.save(output_path, **save_kwargs)
        return output_path.stat().st_size / 1024 / 1024

    new_size = _save(img)

    scale_factor = 0.9
    while new_size > max_size_mb and scale_factor >= 0.4:
        new_width = int(img.size[0] * scale_factor)
        new_height = int(img.size[1] * scale_factor)
        if new_width < 1 or new_height < 1:
            print(
                f"Cannot shrink to valid dimensions at scale {scale_factor:.2f} "
                f"(would be {new_width}x{new_height}); stopping resize loop."
            )
            break

        print(f"Resizing to {new_width}x{new_height} (scale: {scale_factor:.2f})")

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        new_size = _save(resized)

        scale_factor -= 0.1

    print(f"Optimized size: {new_size:.2f}MB")
    pct = (original_size - new_size) / original_size * 100
    print(f"Reduction: {pct:.1f}%")

    if new_size > max_size_mb:
        print(f"\nWARNING: File still larger than {max_size_mb}MB")
        print("Consider:")
        print("  - Lower quality (--quality 70)")
        print("  - Use --file-url instead of local file")
        print("  - Use a smaller or resized image")