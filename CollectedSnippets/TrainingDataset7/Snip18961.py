def new_instance():
            a = Article(pub_date=datetime.today())
            a.save()
            return a