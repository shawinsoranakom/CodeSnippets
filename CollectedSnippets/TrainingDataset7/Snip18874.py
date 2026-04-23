def _user_input(self, input_str):
        """
        Set the environment and the list of command line arguments.

        This sets the bash variables $COMP_WORDS and $COMP_CWORD. The former is
        an array consisting of the individual words in the current command
        line, the latter is the index of the current cursor position, so in
        case a word is completed and the cursor is placed after a whitespace,
        $COMP_CWORD must be incremented by 1:

          * 'django-admin start' -> COMP_CWORD=1
          * 'django-admin startproject' -> COMP_CWORD=1
          * 'django-admin startproject ' -> COMP_CWORD=2
        """
        os.environ["COMP_WORDS"] = input_str
        idx = len(input_str.split(" ")) - 1  # Index of the last word
        comp_cword = idx + 1 if input_str.endswith(" ") else idx
        os.environ["COMP_CWORD"] = str(comp_cword)
        sys.argv = input_str.split()