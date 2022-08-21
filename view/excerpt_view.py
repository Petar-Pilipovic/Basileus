from discord.ext import commands
import discord
import re
from utils import gdoc_handler


# Doesn't work always
def find_first_sentence(text: str, field: str):
    start = text.find(field)
    if start == -1:
        return None

    extended_start = start + len(field)
    first_sentence_regex = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
    sentence = re.split(first_sentence_regex, text[extended_start:])
    return sentence[0]


class ExcerptButtons(discord.ui.View):
    def __init__(self, bot: commands.Bot, author_id: int, url: str):
        super().__init__(timeout=60.0)
        self.bot = bot
        self.author_id = author_id
        self.url = url
        self.status = "RUNNING"
        self.substatus = "NORMAL"
        self.response = None
        self.excerpt = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def on_timeout(self) -> None:
        # print("Excerpt timed out")
        # self.status = "TIMED OUT"
        self.response.embeds[0].set_footer(text="TIMED OUT")
        self.clear_items()
        await self.response.edit(view=self, embed=self.response.embeds[0])

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Auto-Update', style=discord.ButtonStyle.green)
    async def auto_update(self, button: discord.ui.Button, interaction: discord.Interaction):
        doc = gdoc_handler.Document(self.bot.config["Secrets"]["Google API File"])
        text = doc.read_gdoc(self.url)
        fields = ['Description:', 'DESCRIPTION:']  # Common variations

        for field in fields:
            sentence = find_first_sentence(text, field)
            if sentence is not None:  # if regex found a match
                self.excerpt = sentence
                await interaction.response.send_message('Excerpt updated.', ephemeral=True)
                self.response.embeds[0].set_footer(text="SHOWING UPDATED AUTO-EXCERPT")
                await self.response.edit(embed=self.response.embeds[0])
                return

        await interaction.response.send_message('Could not auto-find an excerpt. Try manually adding.', ephemeral=True)
        self.response.embeds[0].set_footer(text="EXCERPT UNABLE TO GENERATE")
        await self.response.edit(embed=self.response.embeds[0])
        return

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Set my own', style=discord.ButtonStyle.blurple)
    async def set_new(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Enter new excerpt (400 characters maximum):', ephemeral=True)

        def check(m):
            # Only work if same user and same channel
            return interaction.channel.id == m.channel.id and interaction.user.id == m.author.id

        def formatter(text: str):
            try:
                return text[:400]  # Technically 401 instead of 400 characters, but this looks cleaner
            except IndexError:
                return text

        user_input = await self.bot.wait_for("message", check=check)
        self.excerpt = formatter(user_input.content)
        await user_input.delete()
        self.response.embeds[0].set_footer(text="SET CUSTOM EMBED")
        await self.response.edit(embed=self.response.embeds[0])
        return

    @discord.ui.button(label='Save & Exit', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Interaction complete.', ephemeral=True)
        print(self.status)
        self.response.embeds[0].set_footer(text="INTERACTION COMPLETE")
        await self.response.edit(view=None, embed=self.response.embeds[0])
        self.stop()
        return
