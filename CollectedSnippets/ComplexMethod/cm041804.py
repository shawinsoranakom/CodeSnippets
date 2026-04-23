def test_skills():
    import sys

    if sys.version_info[:2] == (3, 12):
        print(
            "skills.search is only for python 3.11 for now, because it depends on unstructured. skipping this test."
        )
        return

    import json

    interpreter.llm.model = "gpt-4o-mini"

    messages = ["USER: Hey can you search the web for me?\nAI: Sure!"]

    combined_messages = "\\n".join(json.dumps(x) for x in messages[-3:])
    query_msg = interpreter.chat(
        f"This is the conversation so far: {combined_messages}. What is a hypothetical python function that might help resolve the user's query? Respond with nothing but the hypothetical function name exactly."
    )
    query = query_msg[0]["content"]
    # skills_path = '/01OS/server/skills'
    # interpreter.computer.skills.path = skills_path
    print(interpreter.computer.skills.path)
    if os.path.exists(interpreter.computer.skills.path):
        for file in os.listdir(interpreter.computer.skills.path):
            os.remove(os.path.join(interpreter.computer.skills.path, file))
    print("Path: ", interpreter.computer.skills.path)
    print("Files in the path: ")
    interpreter.computer.run("python", "def testing_skilsl():\n    print('hi')")
    for file in os.listdir(interpreter.computer.skills.path):
        print(file)
    interpreter.computer.run("python", "def testing_skill():\n    print('hi')")
    print("Files in the path: ")
    for file in os.listdir(interpreter.computer.skills.path):
        print(file)

    try:
        skills = interpreter.computer.skills.search(query)
    except ImportError:
        print("Attempting to install unstructured[all-docs]")
        import subprocess

        subprocess.run(["pip", "install", "unstructured[all-docs]"], check=True)
        skills = interpreter.computer.skills.search(query)

    lowercase_skills = [skill[0].lower() + skill[1:] for skill in skills]
    output = "\\n".join(lowercase_skills)
    assert "testing_skilsl" in str(output)