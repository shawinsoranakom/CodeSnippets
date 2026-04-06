def match(command):
    return (not which(command.script_parts[0])
            and 'not found' in command.output
            and os.path.isfile('gradlew'))