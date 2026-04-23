def setUpTestData(cls):
        cls.robin = Scene.objects.create(
            scene="Scene 10", setting="The dark forest of Ewing"
        )
        cls.minstrel = Character.objects.create(name="Minstrel")
        verses = [
            (
                "Bravely bold Sir Robin, rode forth from Camelot. "
                "He was not afraid to die, o Brave Sir Robin. "
                "He was not at all afraid to be killed in nasty ways. "
                "Brave, brave, brave, brave Sir Robin"
            ),
            (
                "He was not in the least bit scared to be mashed into a pulp, "
                "Or to have his eyes gouged out, and his elbows broken. "
                "To have his kneecaps split, and his body burned away, "
                "And his limbs all hacked and mangled, brave Sir Robin!"
            ),
            (
                "His head smashed in and his heart cut out, "
                "And his liver removed and his bowels unplugged, "
                "And his nostrils ripped and his bottom burned off,"
                "And his --"
            ),
        ]
        cls.verses = [
            Line.objects.create(
                scene=cls.robin,
                character=cls.minstrel,
                dialogue=verse,
            )
            for verse in verses
        ]
        cls.verse0, cls.verse1, cls.verse2 = cls.verses

        cls.witch_scene = Scene.objects.create(
            scene="Scene 5", setting="Sir Bedemir's Castle"
        )
        bedemir = Character.objects.create(name="Bedemir")
        crowd = Character.objects.create(name="Crowd")
        witch = Character.objects.create(name="Witch")
        duck = Character.objects.create(name="Duck")

        cls.bedemir0 = Line.objects.create(
            scene=cls.witch_scene,
            character=bedemir,
            dialogue="We shall use my larger scales!",
            dialogue_config="english",
        )
        cls.bedemir1 = Line.objects.create(
            scene=cls.witch_scene,
            character=bedemir,
            dialogue="Right, remove the supports!",
            dialogue_config="english",
        )
        cls.duck = Line.objects.create(
            scene=cls.witch_scene, character=duck, dialogue=None
        )
        cls.crowd = Line.objects.create(
            scene=cls.witch_scene, character=crowd, dialogue="A witch! A witch!"
        )
        cls.witch = Line.objects.create(
            scene=cls.witch_scene, character=witch, dialogue="It's a fair cop."
        )

        trojan_rabbit = Scene.objects.create(
            scene="Scene 8", setting="The castle of Our Master Ruiz' de lu la Ramper"
        )
        guards = Character.objects.create(name="French Guards")
        cls.french = Line.objects.create(
            scene=trojan_rabbit,
            character=guards,
            dialogue="Oh. Un beau cadeau. Oui oui.",
            dialogue_config="french",
        )