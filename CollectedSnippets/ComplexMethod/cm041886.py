def apply_profile(interpreter, profile, profile_path):
    if "start_script" in profile:
        scope = {"interpreter": interpreter}
        exec(profile["start_script"], scope, scope)

    if (
        "version" not in profile or profile["version"] != OI_VERSION
    ):  # Remember to update this version number at the top of the file ^
        print("")
        print(
            "We have updated our profile file format. Would you like to migrate your profile file to the new format? No data will be lost."
        )
        print("")
        message = input("(y/n) ")
        print("")
        if message.lower() == "y":
            migrate_user_app_directory()
            print("Migration complete.")
            print("")
            if profile_path.endswith("default.yaml"):
                with open(profile_path, "r") as file:
                    text = file.read()
                text = text.replace(
                    "version: " + str(profile["version"]), f"version: {OI_VERSION}"
                )

                try:
                    if profile["llm"]["model"] == "gpt-4":
                        text = text.replace("gpt-4", "gpt-4o")
                        profile["llm"]["model"] = "gpt-4o"
                    elif profile["llm"]["model"] == "gpt-4-turbo-preview":
                        text = text.replace("gpt-4-turbo-preview", "gpt-4o")
                        profile["llm"]["model"] = "gpt-4o"
                except:
                    raise
                    pass  # fine

                with open(profile_path, "w") as file:
                    file.write(text)
        else:
            print("Skipping loading profile...")
            print("")
            # If the migration is skipped, add the version number to the end of the file
            if profile_path.endswith("default.yaml"):
                with open(profile_path, "a") as file:
                    file.write(
                        f"\nversion: {OI_VERSION}  # Profile version (do not modify)"
                    )
            return interpreter

    if "system_message" in profile:
        interpreter.display_message(
            "\n**FYI:** A `system_message` was found in your profile.\n\nBecause we frequently improve our default system message, we highly recommend removing the `system_message` parameter in your profile (which overrides the default system message) or simply resetting your profile.\n\n**To reset your profile, run `interpreter --reset_profile`.**\n"
        )
        time.sleep(2)
        interpreter.display_message("---")

    if "computer" in profile and "languages" in profile["computer"]:
        # this is handled specially
        interpreter.computer.languages = [
            i
            for i in interpreter.computer.languages
            if i.name.lower() in [l.lower() for l in profile["computer"]["languages"]]
        ]
        del profile["computer.languages"]

    apply_profile_to_object(interpreter, profile)

    return interpreter