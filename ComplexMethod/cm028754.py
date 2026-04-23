def read_squad_examples(input_file,
                        is_training,
                        version_2_with_negative,
                        translated_input_folder=None):
  """Read a SQuAD json file into a list of SquadExample."""
  del version_2_with_negative
  with tf.io.gfile.GFile(input_file, "r") as reader:
    input_data = json.load(reader)["data"]

  if translated_input_folder is not None:
    translated_files = tf.io.gfile.glob(
        os.path.join(translated_input_folder, "*.json"))
    for file in translated_files:
      with tf.io.gfile.GFile(file, "r") as reader:
        input_data.extend(json.load(reader)["data"])

  examples = []
  for entry in input_data:
    for paragraph in entry["paragraphs"]:
      paragraph_text = paragraph["context"]

      for qa in paragraph["qas"]:
        qas_id = qa["id"]
        question_text = qa["question"]
        start_position = None
        orig_answer_text = None
        is_impossible = False

        if is_training:
          is_impossible = qa.get("is_impossible", False)
          if (len(qa["answers"]) != 1) and (not is_impossible):
            raise ValueError(
                "For training, each question should have exactly 1 answer.")
          if not is_impossible:
            answer = qa["answers"][0]
            orig_answer_text = answer["text"]
            start_position = answer["answer_start"]
          else:
            start_position = -1
            orig_answer_text = ""

        example = SquadExample(
            qas_id=qas_id,
            question_text=question_text,
            paragraph_text=paragraph_text,
            orig_answer_text=orig_answer_text,
            start_position=start_position,
            is_impossible=is_impossible)
        examples.append(example)

  return examples