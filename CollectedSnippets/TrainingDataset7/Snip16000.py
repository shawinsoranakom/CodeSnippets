def clean(self):
        for person_dict in self.cleaned_data:
            person = person_dict.get("id")
            alive = person_dict.get("alive")
            if person and alive and person.name == "Grace Hopper":
                raise ValidationError("Grace is not a Zombie")