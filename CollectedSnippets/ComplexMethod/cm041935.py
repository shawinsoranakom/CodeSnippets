def load_experience(self, path=None, mode: str = "Graph"):
        if mode == "Graph":
            rounds_dir = os.path.join(self.root_path, "workflows")
        else:
            rounds_dir = path

        experience_data = defaultdict(lambda: {"score": None, "success": {}, "failure": {}})

        for round_dir in os.listdir(rounds_dir):
            if os.path.isdir(os.path.join(rounds_dir, round_dir)) and round_dir.startswith("round_"):
                round_path = os.path.join(rounds_dir, round_dir)
                try:
                    round_number = int(round_dir.split("_")[1])
                    json_file_path = os.path.join(round_path, "experience.json")
                    if os.path.exists(json_file_path):
                        data = read_json_file(json_file_path, encoding="utf-8")
                        father_node = data["father node"]

                        if experience_data[father_node]["score"] is None:
                            experience_data[father_node]["score"] = data["before"]

                        if data["succeed"]:
                            experience_data[father_node]["success"][round_number] = {
                                "modification": data["modification"],
                                "score": data["after"],
                            }
                        else:
                            experience_data[father_node]["failure"][round_number] = {
                                "modification": data["modification"],
                                "score": data["after"],
                            }
                except Exception as e:
                    logger.info(f"Error processing {round_dir}: {str(e)}")

        experience_data = dict(experience_data)

        output_path = os.path.join(rounds_dir, "processed_experience.json")
        with open(output_path, "w", encoding="utf-8") as outfile:
            json.dump(experience_data, outfile, indent=4, ensure_ascii=False)

        logger.info(f"Processed experience data saved to {output_path}")
        return experience_data