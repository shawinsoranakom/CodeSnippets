def match(command):
    return bool(re.search(r"src refspec \w+ does not match any", command.output))