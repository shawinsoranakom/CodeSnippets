def setUpClass(cls):
        super().setUpClass()
        cls.no_choices = Choiceful._meta.get_field("no_choices")
        cls.empty_choices = Choiceful._meta.get_field("empty_choices")
        cls.empty_choices_bool = Choiceful._meta.get_field("empty_choices_bool")
        cls.empty_choices_text = Choiceful._meta.get_field("empty_choices_text")
        cls.with_choices = Choiceful._meta.get_field("with_choices")
        cls.with_choices_dict = Choiceful._meta.get_field("with_choices_dict")
        cls.with_choices_nested_dict = Choiceful._meta.get_field(
            "with_choices_nested_dict"
        )
        cls.choices_from_enum = Choiceful._meta.get_field("choices_from_enum")
        cls.choices_from_iterator = Choiceful._meta.get_field("choices_from_iterator")
        cls.choices_from_callable = Choiceful._meta.get_field("choices_from_callable")