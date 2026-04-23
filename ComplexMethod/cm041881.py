def main():
    from interpreter import interpreter

    try:
        start_terminal_interface(interpreter)
    except KeyboardInterrupt:
        try:
            interpreter.computer.terminate()

            if not interpreter.offline and not interpreter.disable_telemetry:
                feedback = None
                if len(interpreter.messages) > 3:
                    feedback = (
                        input("\n\nWas Open Interpreter helpful? (y/n): ")
                        .strip()
                        .lower()
                    )
                    if feedback == "y":
                        feedback = True
                    elif feedback == "n":
                        feedback = False
                    else:
                        feedback = None
                    if feedback != None and not interpreter.contribute_conversation:
                        if interpreter.llm.model == "i":
                            contribute = "y"
                        else:
                            print(
                                "\nThanks for your feedback! Would you like to send us this chat so we can improve?\n"
                            )
                            contribute = input("(y/n): ").strip().lower()

                        if contribute == "y":
                            interpreter.contribute_conversation = True
                            interpreter.display_message(
                                "\n*Thank you for contributing!*\n"
                            )

                if (
                    interpreter.contribute_conversation or interpreter.llm.model == "i"
                ) and interpreter.messages != []:
                    conversation_id = (
                        interpreter.conversation_id
                        if hasattr(interpreter, "conversation_id")
                        else None
                    )
                    contribute_conversations(
                        [interpreter.messages], feedback, conversation_id
                    )

        except KeyboardInterrupt:
            pass
    finally:
        interpreter.computer.terminate()