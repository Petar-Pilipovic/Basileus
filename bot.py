import configparser
from discord import Intents
from discord.ext import commands


# Config load
class Bot(commands.Bot):
    def __init__(self):
        self.reviewers = []  # for type hinting; TODO: delete later
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        super().__init__(command_prefix=self.config['Bot Settings']['Prefix'], intents=Intents.all(), help_command=None)
