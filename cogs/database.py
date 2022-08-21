import random
import bisect

import gspread
from fuzzywuzzy import fuzz, process

import discord
from discord.ext import commands

from view import edit_view
from view import excerpt_view


# TODO: Add automatic updating of database to worksheet
class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        gc = gspread.service_account(filename=bot.config["Secrets"]["Google API File"])
        sh = gc.open_by_key(bot.config["Bot Settings"]["Database URL"])
        self.worksheet = sh.sheet1
        self.database = self.worksheet.get_all_values()

    def make_embed(self, row):
        row_config = self.bot.config['Database Rows']
        made_embed = discord.Embed(colour=self.bot.config['Colours'].getint('Edit'),
                                   title=f"{row[row_config.getint('Prefix')]}-"
                                         f"{row[row_config.getint('Number')]} "
                                         f"{row[row_config.getint('Nickname')]}",
                                   description=row[row_config.getint('Excerpt')])
        made_embed.add_field(name="Object class:", value=row[row_config.getint('Classification')], inline=True)
        made_embed.add_field(name="Clearance level:", value=row[row_config.getint('Level')], inline=True)
        made_embed.add_field(name="Privileges:", value=row[row_config.getint('Privileges')], inline=True)
        made_embed.add_field(name="Location:", value=row[row_config.getint('Location')], inline=True)
        made_embed.add_field(name="Owned by:", value=f"<@{row[row_config.getint('Author ID')]}>", inline=True)
        if str(row[row_config.getint('Faceclaim')]).startswith('http'):
            made_embed.set_thumbnail(url=row[row_config.getint('Faceclaim')])
        if str(row[row_config.getint('Link')]).startswith('http'):
            made_embed.url = row[row_config.getint('Link')]
        return made_embed

    def find_row_by_number(self, number: str):
        number_row = self.bot.config["Database Rows"].getint("Number")
        db = [row[number_row] for row in self.database]  # Extract second column
        db = db[1:]  # Pop headers
        try:
            found_index = db.index(number)
            return self.database[found_index + 1], found_index + 1  # Return row and row number
        except ValueError:
            return None

    async def check_if_scp_owner(self, author_id, scp_row, channel):
        check = int(scp_row[self.bot.config['Database Rows'].getint('Author ID')]) == author_id
        if check:
            return True
        else:
            embed = discord.Embed(title="This SCP does not belong to you.",
                                  colour=self.bot.config['Colours'].getint('Edit'))
            await channel.send(embed=embed)
            return False

    @commands.command(name="db", aliases=["database"])
    async def db_show(self, ctx):
        embed = discord.Embed(colour=self.bot.config['Colours'].getint('Edit'),
                              description=f"You may view the live database by clicking [here]"
                                          f"(https://docs.google.com/spreadsheets/d/"
                                          f"{self.bot.config['Bot Settings']['Database URL']})")
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name="find", aliases=["FIND", "search", "SEARCH"])
    async def find_scp(self, ctx, *, scp_number: str = None):
        if scp_number is not None:
            if scp_number.isnumeric():  # If number entered
                try:
                    scp_row = self.find_row_by_number(scp_number)[0]
                    embed = self.make_embed(scp_row)
                    await ctx.send(embed=embed)
                except TypeError:
                    embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                          title="No SCP exists under that number.")
                    await ctx.send(embed=embed)
                    return
            else:  # If nickname entered
                nicks = [row[self.bot.config["Database Rows"].getint("Nickname")] for row in self.database]
                result = process.extractOne(query=scp_number, choices=nicks, scorer=fuzz.token_set_ratio)
                # result_set = process.extractOne(query=scp_number, choices=nicks, scorer=fuzz.token_set_ratio)
                # result_sort = process.extractOne(query=scp_number, choices=nicks, scorer=fuzz.token_sort_ratio)
                # result_partial = process.extractOne(query=scp_number, choices=nicks, scorer=fuzz.partial_ratio)
                # await ctx.send(f"**Results**\nFlat Ratio: {result}\nToken Set: {result_set}\n"
                #                f"Token Sort: {result_sort}\nRatio Partial: {result_partial}")
                if result[1] > 70:
                    index = nicks.index(result[0])
                    embed = self.make_embed(self.database[index])
                else:
                    embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                          title="No SCP found with given nickname.")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="random", aliases=["random-scp"])
    async def random_scp(self, ctx):
        embed = self.make_embed(random.choice(self.database[1:]))
        await ctx.send(embed=embed)

    @commands.command(name="status", aliases=["list"])
    async def status(self, ctx, target: discord.User = None):
        if target is None:
            target = ctx.author
        slotted = []
        archived = []
        db = self.database[1:]
        for row in db:
            try:
                if int(row[self.bot.config["Database Rows"].getint("Author ID")]) == target.id:
                    row_config = self.bot.config["Database Rows"]
                    to_add = f"[{row[row_config.getint('Prefix')]}-{row[row_config.getint('Number')]} " \
                             f"{row[row_config.getint('Nickname')]}]({row[row_config.getint('Link')]})"
                    if row[row_config.getint('Slotted')] == 'Y':
                        slotted.append(to_add)
                    else:
                        archived.append(to_add)
            except ValueError:
                pass
        print(slotted)
        print(archived)

        embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                              title=f"SCPs belonging to {target.name}")
        slotted_str = '\n'.join(slotted)
        print(slotted_str)
        archived_str = '\n'.join(archived)
        print(archived_str)
        embed.add_field(name="Slotted SCPs:", value=slotted_str, inline=True)
        embed.add_field(name="Archived SCPs:", value=archived_str, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="excerpt")
    async def excerpt(self, ctx, scp_number: str = None):
        if scp_number is not None:
            scp_row = self.find_row_by_number(scp_number)[0]
            if not await self.check_if_scp_owner(author_id=ctx.author.id, scp_row=scp_row, channel=ctx.channel):
                return
            row_config = self.bot.config["Database Rows"]
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                  url=scp_row[row_config.getint('Link')],
                                  title=f"Excerpt of {scp_row[row_config.getint('Prefix')]}-"
                                        f"{scp_row[row_config.getint('Number')]} "
                                        f"{scp_row[row_config.getint('Nickname')]}",
                                  description=scp_row[row_config.getint('Excerpt')])
            embed.set_footer(text="")
            view = excerpt_view.ExcerptButtons(self.bot, ctx.author.id, url=scp_row[row_config.getint('Link')])
            bot_message = await ctx.send(embed=embed, view=view)
            view.response = bot_message
            await view.wait()
            scp_row[row_config.getint('Excerpt')] = view.excerpt
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="faceclaim", aliases=["fc"])
    async def set_faceclaim(self, ctx, scp_number: str = None, fc: str = None):
        if (fc is not None or len(ctx.message.attachments) > 0) and scp_number is not None:
            row_info = self.find_row_by_number(scp_number)
            if row_info is None:
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="No matching SCP.")
                await ctx.send(embed=embed)
                return
            else:
                if not await self.check_if_scp_owner(author_id=ctx.author.id, scp_row=row_info[0], channel=ctx.channel):
                    return
                if len(ctx.message.attachments) > 0:
                    fc = ctx.message.attachments[0]
                    self.database[row_info[1]][self.bot.config["Database Rows"].getint("Faceclaim")] = fc.url
                    await ctx.send("Updated faceclaim! Note: If you delete the attachment, the faceclaim won't work.")
                elif fc.startswith('http'):
                    self.database[row_info[1]][self.bot.config["Database Rows"].getint("Faceclaim")] = fc
                    await ctx.send("Updated faceclaim!")
                else:
                    embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                          title="Invalid formatting of faceclaim.")
                    await ctx.send(embed=embed)
                    return

        elif scp_number is None:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                  title="Missing a link or attachment.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="edit")
    @commands.has_guild_permissions(manage_roles=True)
    async def edit(self, ctx, scp_number: str = None):
        if scp_number is not None:
            try:
                scp_info = self.find_row_by_number(scp_number)  # Have to account for mutability
                scp_row = scp_info[0].copy()
                embed = self.make_embed(scp_row)
                view = edit_view.EditView(self.bot, scp_row, ctx.author.id)
                bot_message = await ctx.send(embed=embed, view=view)

                await view.wait()

                if view.children[0].status is None:
                    ctx.send("Timed out.")
                    return

                while view.children[0].status == "RUNNING":
                    print("New interaction...")
                    view = edit_view.EditView(self.bot, view.children[0].scp_row, ctx.author.id)
                    await bot_message.edit(embed=self.make_embed(view.children[0].scp_row), view=view)
                    await view.wait()
                if view.children[0].status == "EXIT":
                    print("Discarded!")
                    await ctx.send("Changes discarded.")
                    return
                elif view.children[0].status == "SAVE & EXIT":
                    print("Saved!")
                    await ctx.send("Changes saved.")
                    number_row = self.bot.config["Database Rows"].getint("Number")
                    print(self.database[scp_info[1]])
                    print(view.children[0].scp_row[number_row])
                    if not self.database[scp_info[1]][number_row] == view.children[0].scp_row[number_row]:
                        # if number was edited, we have to move the SCP's position in the database
                        print("Number changed")
                        db = [row[1] for row in self.database]
                        db = db[1:]
                        db = [int(x) for x in db if x]  # filter empty stuff and turn into number list
                        self.database.insert(bisect.bisect(db, int(view.children[0].scp_row[number_row])) + 1,
                                             view.children[0].scp_row)
                        self.database.pop(scp_info[1])
                        return
                    else:
                        self.database[scp_info[1]] = view.children[0].scp_row
                        return
                else:  # if None
                    ctx.send("Timed out. Changes discarded.")
                    return
            except ValueError:
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                      title="No SCP exists under that number.")
                await ctx.send(embed=embed)
                return
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="remove", aliases=["delete"])
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_scp(self, ctx, scp_number: str = None):
        if scp_number is not None:
            db_location = self.find_row_by_number(scp_number)[1]
            self.database.pop(db_location)
            await ctx.send(f"Removed SCP-{scp_number} from the database.")
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="archive", aliases=["unarchive", "slot"])  # Handles both, a bit ugly
    @commands.has_guild_permissions(manage_roles=True)
    async def archival(self, ctx, scp_number: str = None):
        if scp_number is not None:
            if ctx.invoked_with == 'unarchive':
                expected_slot = 'N'
                opposite = 'Y'
                word_status = "unarchived"
            else:
                expected_slot = 'Y'
                opposite = 'N'
                word_status = "archived"

            scp_row = self.find_row_by_number(scp_number)[0]
            config_roles = self.bot.config['Database Rows']
            if scp_row[config_roles.getint("Slotted")] == expected_slot:
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                      title=f"{scp_row[config_roles.getint('Prefix')]}-"
                                            f"{scp_row[config_roles.getint('Number')]} has been {word_status}.")
                scp_row[config_roles.getint("Slotted")] = opposite
            else:
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                      title=f"{scp_row[config_roles.getint('Prefix')]}-"
                                            f"{scp_row[config_roles.getint('Number')]} is already {word_status}.")

            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="generate", aliases=["generate-scp", "add-scp"])
    @commands.has_guild_permissions(manage_roles=True)
    async def generate(self, ctx, scp_number: str = None):
        if scp_number is not None:
            row = self.find_row_by_number(scp_number)
            if row is None:  # If unique number
                db = [row[1] for row in self.database]
                db = db[1:]
                db = [int(x) for x in db if x]  # filter empty stuff and turn into int list
                to_insert = ['SCP', scp_number, "N/A", "Site-19", "Euclid", 2,
                             "N/A", "N/A", "Y", "N/A", 0, 0, "N/A", "N/A"]
                self.database.insert(bisect.bisect(db, int(scp_number)) + 1, to_insert)
                print(self.database)
                await ctx.send(f"Added SCP-{scp_number} as a blank. Edit with `{self.bot.command_prefix}edit`.")
            else:
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Number already taken.")
                await ctx.send(embed=embed)
                return
        else:
            embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Missing an SCP number.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="transfer", aliases=["transfer-scp", "transfer-scps", "transfer-acc"])
    @commands.has_guild_permissions(manage_roles=True)
    async def transfer_acc(self, ctx, from_user: discord.User, to_user: discord.User):
        counter = 0
        for row in self.database:
            if row[self.bot.config["Database Rows"].getint("Author ID")] == from_user.id:
                row[self.bot.config["Database Rows"].getint("Author ID")] = to_user.id
                counter += 1
        await ctx.send(f"Transferred a total of {counter} SCP(s) to {to_user.mention}")

    @commands.command(name="update", aliases=["update-db", "update-database"])
    @commands.has_guild_permissions(manage_guild=True)
    async def update_db(self, ctx):
        self.worksheet.update("A1", self.database, raw=False)
        embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Database updated!",
                              url=f"https://docs.google.com/spreadsheets/d/"
                                  f"{self.bot.config['Bot Settings']['Database URL']}")
        await ctx.send(embed=embed)
        return

    @commands.command(name="reload")
    @commands.has_guild_permissions(manage_guild=True)
    async def reload_db(self, ctx):
        self.database = self.worksheet.get_all_values()
        embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"), title="Internal database reloaded!")
        await ctx.send(embed=embed)

    @commands.command(name="validity-check", aliases=["vc"])
    @commands.has_guild_permissions(manage_guild=True)
    async def check_owners(self, ctx, force_flag: bool = False):
        guild = self.bot.get_guild(self.bot.config["Bot Settings"].getint("Main Server"))
        db = self.database[1:]
        row_config = self.bot.config["Database Rows"]
        counter = 0
        notice = []
        for row in db:
            if guild.get_member(row[row_config.getint("Author ID")]) is not None:  # if Member found in Guild
                pass
            else:
                if force_flag:  # should the bot delete
                    number = row[row_config.getint("Number")]
                    await self.bot.invoke(self.bot.get_command('remove'), scp_number=number)
                    counter += 1
                else:
                    notice.append(f"{row[row_config.getint('Prefix')]}-{row[row_config.getint('Number')]}"
                                  f" {row[row_config.getint('Nickname')]}")
        try:
            if force_flag:
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                      title=f"Removed a total of {counter} SCP(s).")
            else:
                notice_str = '\n'.join(notice)
                embed = discord.Embed(colour=self.bot.config["Colours"].getint("Edit"),
                                      description=f"Invalid entries:\n{notice_str}")
            await ctx.send(embed=embed)
        except (discord.HTTPException, discord.ext.commands.CommandInvokeError):
            await ctx.send(f"A total of {len(notice)} SCPs were found invalid - Too many to write.\n"
                           f"Is this bot is on the main server? If yes, there's a code issue.")
            return


def setup(bot):
    bot.add_cog(Database(bot))
