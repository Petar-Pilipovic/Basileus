from discord.ext import commands
import discord


class Dropdown(discord.ui.Select):
    def __init__(self, bot, scp_row):

        # Set the options that will be presented inside the dropdown
        self.bot = bot
        self.scp_row = scp_row
        self.status = None
        options = [
            discord.SelectOption(label="Change Prefix",
                                 description="Edit the prefix of the SCP.",
                                 emoji='⬆',
                                 value=self.bot.config["Database Rows"].getint("Prefix")),
            discord.SelectOption(label="Change Number",
                                 description="Edit the number of the SCP.",
                                 emoji='🔖',
                                 value=self.bot.config["Database Rows"].getint("Number")),
            discord.SelectOption(label="Change Nickname",
                                 description="Edit the nickname of the SCP.",
                                 emoji='👣',
                                 value=self.bot.config["Database Rows"].getint("Nickname")),
            discord.SelectOption(label="Change Location",
                                 description="Edit the location of the SCP.",
                                 emoji='🏠',
                                 value=self.bot.config["Database Rows"].getint("Location")),
            discord.SelectOption(label="Change Classification",
                                 description="Edit the object class of the SCP.",
                                 emoji='⚠',
                                 value=self.bot.config["Database Rows"].getint("Classification")),
            discord.SelectOption(label="Change Clearance Level",
                                 description="Edit the clearance level of the SCP.",
                                 emoji='㊙',
                                 value=self.bot.config["Database Rows"].getint("Level")),
            discord.SelectOption(label="Change Author ID",
                                 description="Edit who's the author of the SCP.",
                                 emoji='✍',
                                 value=self.bot.config["Database Rows"].getint("Author ID")),
            discord.SelectOption(label="Change Privileges",
                                 description="Edit, or remove, the privileges of the SCP.",
                                 emoji='💎',
                                 value=self.bot.config["Database Rows"].getint("Privileges")),
            # discord.SelectOption(label="",
            #                      description="",
            #                      emoji='🟦',
            #                      value=self.bot.config["Database Rows"].getint("Slotted")),
            discord.SelectOption(label="Change Link",
                                 description="Edit the link of the SCP.",
                                 emoji='🌐',
                                 value=self.bot.config["Database Rows"].getint("Link")),
            # discord.SelectOption(label="",
            #                      description="",
            #                      emoji='🟦',
            #                      value=self.bot.config["Database Rows"].getint("Times Breached")),
            # discord.SelectOption(label="",
            #                      description="",
            #                      emoji='🟦',
            #                      value=self.bot.config["Database Rows"].getint("Research Logs")),
            discord.SelectOption(label="Change Faceclaim",
                                 description="Edit, or remove, the faceclaim of the SCP.",
                                 emoji='💄',
                                 value=self.bot.config["Database Rows"].getint("Faceclaim")),
            discord.SelectOption(label="Change Excerpt",
                                 description="Edit, or remove, the excerpt of the SCP.",
                                 emoji='💬',
                                 value=self.bot.config["Database Rows"].getint("Excerpt")),
            discord.SelectOption(label="Exit without saving",
                                 description="",
                                 emoji='➖',
                                 value='EXIT'),
            discord.SelectOption(label="Save and exit",
                                 description="Exit the edit interface and update the database accordingly.",
                                 emoji='💚',
                                 value='SAVE & EXIT')
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose what to edit...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        if self.values[0] == "SAVE & EXIT" or self.values[0] == "EXIT":
            print("Changed status")
            self.status = self.values[0]
            self.view.stop()
        else:
            response = interaction.response
            await response.send_message('Enter new value:', ephemeral=True)

            def check(m):
                # Only work if same user and channel
                return interaction.channel.id == m.channel.id and interaction.user.id == m.author.id

            def formatter(row: int, value: str):
                rows = self.bot.config["Database Rows"]
                if row == rows.getint("Prefix"):
                    return value.upper()
                elif row == rows.getint("Nickname") and not value.startswith('"'):
                    return str('"' + value + '"')
                return value

            user_message = await self.bot.wait_for("message", check=check)
            self.scp_row[int(self.values[0])] = formatter(int(self.values[0]), user_message.content)
            await user_message.delete()
            self.status = "RUNNING"
            self.view.stop()


class EditView(discord.ui.View):
    def __init__(self, bot: commands.Bot, scp_row, author_id):
        super().__init__()
        self.author_id = author_id
        # Add dropdown to view object
        self.add_item(Dropdown(bot, scp_row))

    # async def on_timeout(self) -> None:
    #     return

    # Check if author of edit is interacting
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id
