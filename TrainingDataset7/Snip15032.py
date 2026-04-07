def validate_env(checkout_dir):
    if not checkout_dir:
        sys.exit("Error: checkout directory not provided (--checkout-dir).")
    if not os.path.exists(checkout_dir):
        sys.exit(f"Error: checkout directory '{checkout_dir}' does not exist.")
    if not os.path.isdir(checkout_dir):
        sys.exit(f"Error: '{checkout_dir}' is not a directory.")