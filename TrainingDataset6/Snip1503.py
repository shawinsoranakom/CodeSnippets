def reset(path):
        with open(path, 'w') as fh:
            lines = [
                '123.234.567.890 asdjkasjdakjsd\n'
                '98.765.432.321 ejioweojwejrosj\n'
                '111.222.333.444 qwepoiwqepoiss\n'
            ]
            fh.writelines(lines)