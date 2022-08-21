from discord.ext import commands, tasks
import discord
import pytz
from datetime import datetime
import bot as b


class MiscCog(commands.Cog):
    def __init__(self, bot: b.Bot):
        self.bot = bot

    async def update_member_count(self):
        guild = self.bot.get_guild(self.bot.config['Bot Settings'].getint('Main Server'))
        member_count_channel = self.bot.get_channel(self.bot.config["Channels"].getint("Clock Channel"))
        member_count = len([member for member in guild.members if not member.bot])  # guild.member_count includes bots
        await member_count_channel.edit(name=f"Member Count: {member_count}")

    @commands.Cog.listener()
    async def on_member_leave(self):
        await self.update_member_count()

    @commands.Cog.listener()
    async def on_member_join(self):
        await self.update_member_count()

    @tasks.loop(minutes=3)
    async def et_clock(self):
        clock_channel = self.bot.get_channel(self.bot.config["Channels"].getint("Clock Channel"))
        et_timezone = pytz.timezone("US/Eastern")
        local_datetime = datetime.now(tz=et_timezone)
        time_to_set = local_datetime.strftime("%a %I:%M %p EST - %m/%d")
        await clock_channel.edit(name=time_to_set)

    @commands.command(name="start-clock")
    async def start_clock(self, ctx):
        await self.et_clock.start()

    @commands.command(name="purge", aliases=["nuke"])
    @commands.has_guild_permissions(kick_members=True)
    async def purge(self, ctx):
        guild = self.bot.get_guild(self.bot.config['Bot Settings'].getint('Main Server'))
        inactive_role = guild.get_role(self.bot.config['Bot Settings'].getint('Inactivity Role'))
        kick_counter = 0
        async with ctx.typing():
            for member in inactive_role.members:
                await member.kick(reason="Inactivity purge")
                kick_counter += 1
            await ctx.send(f"Kicked a total of {kick_counter} inactive members.")


def setup(bot):
    bot.add_cog(MiscCog(bot))
