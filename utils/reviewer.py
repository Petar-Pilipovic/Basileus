from discord.ext import commands
import discord


class Case:
    in_queue_emoji = "⏩"
    under_review_emoji = "⏸"
    case_status = {
        'QUEUE': 1,
        'ACTIVE': 2,
        'RESOLVED': 3
    }

    def __init__(self, origin: discord.Message, thread: discord.Thread = None, handlers: [discord.Member] = None):
        self.status_code = self.case_status['QUEUE']
        self.origin = origin
        self.thread = thread
        if handlers is None:
            self.handlers = []
        else:
            self.handlers = handlers  # First handler is always the primary one

    async def close_case(self):
        print("Closing case!")
        self.status_code = self.case_status['RESOLVED']
        await self.thread.edit(archived=True)
        await self.origin.clear_reaction(self.under_review_emoji)
        return self.handlers

    async def open_case(self, primary: discord.Member, secondary: discord.Member, helper_channel: discord.TextChannel):
        print("Opening case!")
        self.status_code = self.case_status['ACTIVE']
        await self.origin.clear_reaction(self.in_queue_emoji)
        await self.origin.add_reaction(self.under_review_emoji)
        self.handlers.append(primary)
        self.handlers.append(secondary)
        message = f"**SUBMISSION REVIEW**\n" \
                  f"> Primary reviewer:{primary.mention}\n" \
                  f"> Secondary reviewer:{secondary.mention}\n\n" \
                  f"**Intro**\n" \
                  f"> The Primary reviewer is in charge of the submission and it is their duty for it to be reviewed " \
                  f"under 24 hours (When another reviewer will be brought) or, at most, " \
                  f"48 hours (When the entire review team gets pinged).\n" \
                  f"> The Secondary reviewer is tasked with aiding and serving as a second opinion to the Primary." \
                  f"> Feel free to contact anyone in {helper_channel.mention} if specialized expertise is needed.\n\n" \
                  f"**Commands**\n" \
                  f"> Use `close` to finish this thread once a review has been delivered. " \
                  f"This will *archive* this thread. Do **not** do this if the applicant isn't expected to resubmit. " \
                  f"This ***must*** be ran by the **Primary Reviewer** as it resets the user to be Available.\n" \
                  f"**Submission from {self.origin.author.mention}:**"
        case_thread = await helper_channel.create_thread(name=f"Review by {primary.name} for {self.origin.author.name}",
                                                         type=discord.ChannelType.public_thread)
        await case_thread.send(message)
        await case_thread.send(self.origin.content)
        self.thread = case_thread


class Reviewer:
    reviewer_status = {
        'AVAILABLE': 1,
        'UNAVAILABLE': 2,
        'HIATUS': 3
    }

    def __init__(self, reviewer: discord.Member = None, primary_case=None,
                 secondary_case=None):
        self.status_code = self.reviewer_status['AVAILABLE']
        self.reviewer = reviewer

        self.primary = primary_case
        if secondary_case is None:
            self.secondary = []
        else:
            self.secondary = secondary_case

    def assign_case(self, case: Case, is_primary: bool = False):
        if is_primary and self.primary is None:
            self.primary = case
            self.status_code = self.reviewer_status['UNAVAILABLE']
        elif not is_primary:
            self.secondary.append(case)

    def status_change(self, new_status: int):
        if self.status_code == new_status:
            return "You're already marked with that status!"
        else:
            self.status_code = new_status
            return "Status changed!"

    def unassign_case(self, case: Case):
        if self.primary is not None and case.thread.id == self.primary.thread.id:
            self.primary = None
            self.status_change(self.reviewer_status["AVAILABLE"])
            return True
        else:
            # print(f"TO REMOVE: {case}")
            # print(f"CURRENT SECONDARIES: {self.secondary}")
            # secondaries_id = [id(x) for x in self.secondary]
            # idx = secondaries_id.index(id(case))
            self.secondary.remove(case)
            return False
