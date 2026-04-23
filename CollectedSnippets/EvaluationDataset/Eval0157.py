def main() -> None:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    original = cv2.imread(os.path.join(dir_path, "image_data/original_image.png"))
    contrast = cv2.imread(os.path.join(dir_path, "image_data/compressed_image.png"), 1)

    original2 = cv2.imread(os.path.join(dir_path, "image_data/PSNR-example-base.png"))
    contrast2 = cv2.imread(
        os.path.join(dir_path, "image_data/PSNR-example-comp-10.jpg"), 1
    )

    print("-- First Test --")
    print(f"PSNR value is {peak_signal_to_noise_ratio(original, contrast)} dB")

    print("\n-- Second Test --")
    print(f"PSNR value is {peak_signal_to_noise_ratio(original2, contrast2)} dB")
