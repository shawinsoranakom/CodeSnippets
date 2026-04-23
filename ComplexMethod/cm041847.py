def import_skills(self):
        """
        [INTERNAL METHOD - NOT FOR Assistant USE]
        System initialization method that imports all Python files from the skills directory.

        This method is called automatically during system setup to load available skills.
        Assistant should use list(), search(), or call skills directly instead of this method.
        """
        if not self.computer.import_skills:
            return

        previous_save_skills_setting = self.computer.save_skills

        self.computer.save_skills = False

        # Make sure it's not over 100mb
        total_size = 0
        for path, dirs, files in os.walk(self.path):
            for f in files:
                fp = os.path.join(path, f)
                total_size += os.path.getsize(fp)
        total_size = total_size / (1024 * 1024)  # convert bytes to megabytes
        if total_size > 100:
            raise Warning(
                f"Skills at path {self.path} can't exceed 100mb. Try deleting some."
            )

        code_to_run = ""
        for file in glob.glob(os.path.join(self.path, "*.py")):
            with open(file, "r") as f:
                code_to_run += f.read() + "\n"

        if self.computer.interpreter.debug:
            print("IMPORTING SKILLS:\n", code_to_run)

        output = self.computer.run("python", code_to_run)

        if "traceback" in str(output).lower():
            # Import them individually
            for file in glob.glob(os.path.join(self.path, "*.py")):
                with open(file, "r") as f:
                    code_to_run = f.read() + "\n"

                if self.computer.interpreter.debug:
                    print(self.path)
                    print("IMPORTING SKILL:\n", code_to_run)

                output = self.computer.run("python", code_to_run)

                if "traceback" in str(output).lower():
                    print(
                        f"Skill at {file} might be broken— it produces a traceback when run."
                    )

        self.computer.save_skills = previous_save_skills_setting