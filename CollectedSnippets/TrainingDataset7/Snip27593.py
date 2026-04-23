def get_base_project_state(self):
        new_apps = Apps()

        class User(models.Model):
            class Meta:
                app_label = "tests"
                apps = new_apps

        class Comment(models.Model):
            text = models.TextField()
            user = models.ForeignKey(User, models.CASCADE)
            comments = models.ManyToManyField("self")

            class Meta:
                app_label = "tests"
                apps = new_apps

        class Post(models.Model):
            text = models.TextField()
            authors = models.ManyToManyField(User)

            class Meta:
                app_label = "tests"
                apps = new_apps

        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(User))
        project_state.add_model(ModelState.from_model(Comment))
        project_state.add_model(ModelState.from_model(Post))
        return project_state