import bot as b
import os
from utils import reviewer

bot = b.Bot()

# Load all cogs from ./cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        cog = f'cogs.{filename[:-3]}'
        bot.load_extension(cog)
        print(f"Loaded an extension: {cog}")


async def on_startup():
    await bot.wait_until_ready()
    main_guild = bot.get_guild(bot.config["Bot Settings"].getint("Main Server"))
    helper_role = main_guild.get_role(bot.config["Bot Settings"].getint("Character Helper Role"))
    bot.reviewers = [reviewer.Reviewer(member) for member in helper_role.members]


bot.loop.create_task(on_startup())  # Runs the task once. More reliable than on_ready
bot.run(bot.config['Secrets']['Discord Bot Token'])
