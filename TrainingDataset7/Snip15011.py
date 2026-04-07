def cmdline_to_win(line):
            if line.startswith("# "):
                return "REM " + args_to_win(line[2:])
            if line.startswith("$ # "):
                return "REM " + args_to_win(line[4:])
            if line.startswith("$ ./manage.py"):
                return "manage.py " + args_to_win(line[13:])
            if line.startswith("$ manage.py"):
                return "manage.py " + args_to_win(line[11:])
            if line.startswith("$ ./runtests.py"):
                return "runtests.py " + args_to_win(line[15:])
            if line.startswith("$ ./"):
                return args_to_win(line[4:])
            if line.startswith("$ python3"):
                return "py " + args_to_win(line[9:])
            if line.startswith("$ python"):
                return "py " + args_to_win(line[8:])
            if line.startswith("$ "):
                return args_to_win(line[2:])
            return None