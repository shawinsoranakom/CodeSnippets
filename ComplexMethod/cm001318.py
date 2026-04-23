def organize_files(directory_path):
    # Define file type groups
    file_types = {
        "images": [".png", ".jpg", ".jpeg"],
        "documents": [".pdf", ".docx", ".txt"],
        "audio": [".mp3", ".wav", ".flac"],
    }

    # Create the folders if they don't exist
    for folder_name in file_types.keys():
        folder_path = os.path.join(directory_path, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Traverse through all files and folders in the specified directory
    for foldername, subfolders, filenames in os.walk(directory_path):
        for filename in filenames:
            # Get file extension
            _, file_extension = os.path.splitext(filename)

            # Move files to corresponding folders
            for folder_name, extensions in file_types.items():
                if file_extension in extensions:
                    old_path = os.path.join(foldername, filename)
                    new_path = os.path.join(directory_path, folder_name, filename)
                    if old_path != new_path:
                        shutil.move(old_path, new_path)