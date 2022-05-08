import disnake
from disnake.ext.commands import CheckFailure


class NoVoiceConnection(CheckFailure):
    pass


class DifferentVoiceChannel(CheckFailure):
    pass


class InvalidURL(CheckFailure):
    pass


class NotMyCreator(CheckFailure):
    pass
