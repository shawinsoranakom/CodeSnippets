def load_spacy_model():
    import spacy

    name = "models/reuters"
    home_folder = get_home_folder()
    model_folder = Path(home_folder) / name

    # Check if the model directory already exists
    if not (model_folder.exists() and any(model_folder.iterdir())):
        repo_url = "https://github.com/unclecode/crawl4ai.git"
        branch = MODEL_REPO_BRANCH
        repo_folder = Path(home_folder) / "crawl4ai"

        print("[LOG] ⏬ Downloading Spacy model for the first time...")

        # Remove existing repo folder if it exists
        if repo_folder.exists():
            try:
                shutil.rmtree(repo_folder)
                if model_folder.exists():
                    shutil.rmtree(model_folder)
            except PermissionError:
                print(
                    "[WARNING] Unable to remove existing folders. Please manually delete the following folders and try again:"
                )
                print(f"- {repo_folder}")
                print(f"- {model_folder}")
                return None

        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", "-b", branch, repo_url, str(repo_folder)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            # Create the models directory if it doesn't exist
            models_folder = Path(home_folder) / "models"
            models_folder.mkdir(parents=True, exist_ok=True)

            # Copy the reuters model folder to the models directory
            source_folder = repo_folder / "models" / "reuters"
            shutil.copytree(source_folder, model_folder)

            # Remove the cloned repository
            shutil.rmtree(repo_folder)

            print("[LOG] ✅ Spacy Model downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while cloning the repository: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    try:
        return spacy.load(str(model_folder))
    except Exception as e:
        print(f"Error loading spacy model: {e}")
        return None