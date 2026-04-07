def test_cache17(self):
        """
        Regression test for #11270.
        """
        output = self.engine.render_to_string(
            "cache17",
            {
                "poem": (
                    "Oh freddled gruntbuggly/Thy micturations are to me/"
                    "As plurdled gabbleblotchits/On a lurgid bee/"
                    "That mordiously hath bitled out/Its earted jurtles/"
                    "Into a rancid festering/Or else I shall rend thee in the "
                    "gobberwarts with my blurglecruncheon/See if I don't."
                ),
            },
        )
        self.assertEqual(output, "Some Content")