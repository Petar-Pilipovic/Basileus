from discord.ext import commands
import discord

import random
import asyncio
import bot as b

from utils import reviewer


class Submissions(commands.Cog):
    def __init__(self, bot: b.Bot):
        self.bot = bot
        self.cases = []
        self.in_queue_emoji = reviewer.Case.in_queue_emoji
        self.under_review_emoji = reviewer.Case.under_review_emoji

    def get_reviewers_by_status(self, status: int):
        by_status = [x for x in self.bot.reviewers if x.status_code == status]
        return by_status

    def get_queued_cases(self):
        queued_cases = [x for x in self.cases if x.status_code == reviewer.Case.case_status["QUEUE"]]
        return queued_cases

    def new_helper_embed(self):
        embed = discord.Embed(title="Reviewer listing",
                              description="Refer to the [documentation](https://docs.google.com/document/d/"
                                          "1dFMvCb1Y2al1dzX2EHNbAOLdProZnXJq8SngD8CDNeI/edit?usp=sharing)"
                                          " for a better understanding regarding what's going on")
        available = [av.reviewer.mention for av in self.bot.reviewers
                     if av.status_code == reviewer.Reviewer.reviewer_status['AVAILABLE']]
        unavailable = [av.reviewer.mention for av in self.bot.reviewers
                       if av.status_code == reviewer.Reviewer.reviewer_status['UNAVAILABLE']]
        hiatus = [av.reviewer.mention for av in self.bot.reviewers
                  if av.status_code == reviewer.Reviewer.reviewer_status['HIATUS']]

        if len(available) > 0:
            available_str = '\n'.join(available)
        else:
            available_str = "None"

        if len(unavailable) > 0:
            unavailable_str = '\n'.join(unavailable)
        else:
            unavailable_str = "None"

        if len(hiatus) > 0:
            hiatus_str = '\n'.join(hiatus)
        else:
            hiatus_str = "None"

        embed.add_field(name="Available reviewers:", value=available_str, inline=True)
        embed.add_field(name="Busy reviewers:", value=unavailable_str, inline=True)
        embed.add_field(name="Reviewers on hiatus:", value=hiatus_str, inline=True)
        return embed

    async def case_reminders(self, case: reviewer.Case):
        await asyncio.sleep((60*24*24))
        if case.status_code == reviewer.Case.case_status['ACTIVE']:
            candidates = list(set(self.bot.reviewers - [reviewer.Reviewer(reviewer=x) for x in case.handlers] -
                                  self.get_reviewers_by_status(reviewer.Reviewer.reviewer_status["HIATUS"])))
            tertiary = random.choice(candidates)
            await case.thread.send(f"**This is your 24-hour warning.**\n"
                                   f"An additional reviewer has been assigned - {tertiary.mention}.\n"
                                   f"They are to ensure that you, {case.handlers[0].mention} and "
                                   f"{case.handlers[1].mention}, finish the submission soon.")
            await asyncio.sleep((60*24*24))
        else:
            return

        if case.status_code == reviewer.Case.case_status['ACTIVE']:
            guild = case.origin.guild
            helper_role = guild.get_role(self.bot.config["Bot Settings"].getint("Character Helper Role"))
            await case.thread.send(f"**48 hours have passed since the submission has been submitted.**\n"
                                   f"{helper_role.mention}")
            return
        return

    async def assign_to_reviewer(self, primary: reviewer.Reviewer, case: reviewer.Case):
        # Assign logic
        # print(f"ASSIGNING: {self.cases}")
        # print("Assigning...")
        on_hiatus = self.get_reviewers_by_status(reviewer.Reviewer.reviewer_status["HIATUS"])
        candidates = [item for item in self.bot.reviewers if item not in on_hiatus and not item == primary]
        # candidates.remove(primary)
        secondary = random.choice(candidates)
        # print(f"Secondary reviewer: {secondary.reviewer.name}")
        primary.assign_case(is_primary=True, case=case)
        secondary.assign_case(case=case)
        main_guild = self.bot.get_guild(self.bot.config["Bot Settings"].getint("Main Server"))
        ch_channel = main_guild.get_channel(self.bot.config["Channels"].getint("Character Helper Hub"))
        await case.open_case(primary=primary.reviewer, secondary=secondary.reviewer,
                             helper_channel=ch_channel)
        # print(f"2nd Reviewer's cases: {secondary.secondary}")
        self.cases.append(case)
        # print("Setting reminders...")
        asyncio.create_task(self.case_reminders(case))
        # print(f"FINISHED ASSIGNING: {self.cases}")
        return

    @commands.Cog.listener()
    async def on_message(self, submission: discord.Message):
        main_guild = self.bot.get_guild(self.bot.config["Bot Settings"].getint("Main Server"))
        oc_subs = main_guild.get_channel(self.bot.config["Channels"].getint("OC Subs"))
        scp_subs = main_guild.get_channel(self.bot.config["Channels"].getint("SCP Subs"))
        misc_subs = main_guild.get_channel(self.bot.config["Channels"].getint("Misc Subs"))
        if submission.channel in [oc_subs, scp_subs, misc_subs] and not submission.author.bot:
            await submission.add_reaction(self.in_queue_emoji)
            available_list = self.get_reviewers_by_status(reviewer.Reviewer.reviewer_status['AVAILABLE'])
            if len(available_list) > 0:
                await self.assign_to_reviewer(primary=random.choice(available_list), case=reviewer.Case(submission))
            else:
                self.cases.append(reviewer.Case(submission))
                await submission.add_reaction(self.in_queue_emoji)

    @commands.command(name="close")
    @commands.has_guild_permissions(manage_roles=True)
    async def close_submission(self, ctx):
        if type(ctx.channel) is not discord.threads.Thread:
            await ctx.send("Command not being invoked within an active reviewing thread.")
            return
        else:
            # try:
            # print([c.handlers for c in self.cases])
            all_case_threads = [c.thread.id for c in self.cases if not c.status_code == reviewer.Case.case_status["QUEUE"]]

            result = all_case_threads.index(ctx.channel.id)
            print(f"Result: {result}")
            ctx_case = self.cases[result]
            self.cases.pop(result)
            # print(f"CTX_CASE: {ctx_case}")

            case_handlers = await ctx_case.close_case()
            case_reviewers = [r for r in self.bot.reviewers if r.reviewer in case_handlers]
            # print(f"CLOSING CASE, SECONDARIES PRINT: {case_reviewers[1].secondary}")
            queued_cases = self.get_queued_cases()
            for case_reviewer in case_reviewers:
                is_now_available = case_reviewer.unassign_case(case=ctx_case)
                if is_now_available and len(queued_cases) > 0:
                    await self.assign_to_reviewer(primary=case_reviewer, case=queued_cases[0])
            # except ValueError:
            #     await ctx.send("Command not being invoked within an active reviewing thread.")

    @commands.command(name="ch-available", aliases=["available", "aval"])
    @commands.has_guild_permissions(manage_roles=True)
    async def ch_active(self, ctx: discord.ext.commands.Context, target: discord.Member = None):
        if target is None:
            target = ctx.author
        reviewers = [x.reviewer for x in self.bot.reviewers]
        try:
            index = reviewers.index(target)
            self.bot.reviewers[index].status_change(reviewer.Reviewer.reviewer_status["AVAILABLE"])
            await ctx.send("Marked as available.")
            queued_submissions = self.get_queued_cases()
            if len(queued_submissions) > 0:
                await self.assign_to_reviewer(primary=self.bot.reviewers[index], case=queued_submissions[0])
        except ValueError:
            await ctx.send("Not listed as a reviewer.")

    @commands.command(name="ch-unavailable", aliases=["unavailable", "unaval", "unav"])
    @commands.has_guild_permissions(manage_roles=True)
    async def ch_inactive(self, ctx: discord.ext.commands.Context, target: discord.Member = None):
        if target is None:
            target = ctx.author
        reviewers = [x.reviewer for x in self.bot.reviewers]
        try:
            index = reviewers.index(target)
            self.bot.reviewers[index].status_change(reviewer.Reviewer.reviewer_status["UNAVAILABLE"])
            await ctx.send("Marked as unavailable.")
        except ValueError:
            await ctx.send("Not listed as a reviewer.")

    @commands.command(name="ch-hiatus", aliases=["ch-haitus", "hiatus", "haitus"])
    @commands.has_guild_permissions(manage_roles=True)
    async def ch_hiatus(self, ctx: discord.ext.commands.Context, target: discord.Member = None):
        if target is None:
            target = ctx.author
        reviewers = [x.reviewer for x in self.bot.reviewers]
        try:
            index = reviewers.index(target)
            if self.bot.reviewers[index].status_code == 'UNAVAILABLE' and target == ctx.author:
                await ctx.send("You can't go on hiatus while having an active case.")
            else:
                self.bot.reviewers[index].status_change(reviewer.Reviewer.reviewer_status["HIATUS"])
                await ctx.send("Marked as on hiatus.")
        except ValueError:
            await ctx.send("Not listed as a reviewer.")

    @commands.command(name="ch-assign", aliases=["assign", "case-assign"])
    @commands.has_guild_permissions(manage_guild=True)
    async def manual_case_assign(self, ctx, submission: discord.Message = None):
        if submission is None:
            await ctx.send("No submission supplied.")
            return
        else:
            await submission.clear_reactions()
            await submission.add_reaction(self.in_queue_emoji)
            available_list = self.get_reviewers_by_status(reviewer.Reviewer.reviewer_status['AVAILABLE'])
            if len(available_list) > 0:
                await self.assign_to_reviewer(primary=random.choice(available_list), case=reviewer.Case(submission))
                await ctx.send("Assigned reviewer to case.")
            else:
                self.cases.append(reviewer.Case(submission))
                await submission.add_reaction(self.in_queue_emoji)
                await ctx.send("Case has been put into queue.")

    @commands.command(name="add-ch")
    @commands.has_guild_permissions(manage_guild=True)
    async def add_helper(self, ctx, target: discord.Member = None):
        if target is None:
            await ctx.send("No new helper supplied.")
            return
        else:
            new_rew = reviewer.Reviewer(reviewer=target)
            self.bot.reviewers.append(new_rew)
            queued_submissions = self.get_queued_cases()
            if len(queued_submissions) > 0:
                await self.assign_to_reviewer(self.bot.reviewers[-1], reviewer.Case(queued_submissions[0]))
            return

    @commands.command(name="ch-status", aliases=["show", "ch-show"])
    @commands.has_guild_permissions(manage_roles=True)
    async def show_helper_status(self, ctx):
        embed = self.new_helper_embed()
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Submissions(bot))
