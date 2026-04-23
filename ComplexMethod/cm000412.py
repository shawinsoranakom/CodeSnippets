def test_all_platforms_exist(self):
        assert Platform.DISCORD.value == "DISCORD"
        assert Platform.TELEGRAM.value == "TELEGRAM"
        assert Platform.SLACK.value == "SLACK"
        assert Platform.TEAMS.value == "TEAMS"
        assert Platform.WHATSAPP.value == "WHATSAPP"
        assert Platform.GITHUB.value == "GITHUB"
        assert Platform.LINEAR.value == "LINEAR"