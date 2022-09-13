from asyncio import TimeoutError

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from pony import orm
from pony.orm import db_session, select

from utils.converters import MemberConverter
from utils.embed import Embed
from utils.models import Report, ReportStatus
from utils.paginators import Paginator


class Feedback(discord.ui.Modal, title='Feedback ticket'):
    # short input, required
    subject = discord.ui.TextInput(
        label='Title',
        placeholder='Short description of issue.',
        max_length=50
    )

    # longer input, not required
    feedback = discord.ui.TextInput(
        label='Description',
        style=discord.TextStyle.long,
        placeholder='Long description of issue.',
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        with db_session:
            report = Report(title=self.subject.value, description=self.feedback.value, author=interaction.user.id)
        await interaction.response.send_message(
            f'Thank you! Your feedback has been recorded. You can check the status via /report view {report.id}.',
            ephemeral=True
        )

        # todo: avoid hardcoding id
        creator = interaction.client.get_user(254207115399397376)
        await creator.send(f"New report #{report.id} from {interaction.user}.")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        # print(error)
        # traceback.print_tb(error.__traceback__)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(3, 45, BucketType.user)
    @commands.command()
    async def purge(self, ctx, amount: int = None):
        """Utility|Deletes a number of messages.|Manage messages permission"""
        if not amount:
            text = "You have to enter the number of messages you want to delete."
            return await ctx.send(text)
        if amount >= 100:
            amount = 100
        await ctx.message.channel.purge(limit=amount)
        text = "I made {} messages to disappear. Am I magic or not? :eyes:"
        await ctx.send(text.format(amount), delete_after=3.0)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.command()
    async def kick(self, ctx, target: MemberConverter = None, *, reason=None):
        """Utility|Kicks a member.|Kick permission"""

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.message.channel

        if not target:
            text = "I don't know who you want me to kick!"
            return await ctx.send(text)
        if target == ctx.author:
            text = "You shouldn't kick yourself."
            return await ctx.send(text)
        if target.top_role > ctx.author.top_role:
            return await ctx.send("You shouldn't kick your superiors!")
        if target.top_role >= ctx.me.top_role:
            return await ctx.send(f"I can't kick {target} as their role is greater than/equal to my role.")

        if not reason:
            reason = "Unknown"
        text = f"Are you sure you want to kick **{target}**, for reason *{reason}*?\nIf yes, type `confirm`."
        await ctx.send(text)
        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=20)
        except TimeoutError:
            await ctx.send("I'll take this as a no...")
        else:
            if cf_mes.content.lower() != "confirm":
                text = "{} got away from the kick, *for now*."
                return await ctx.send(text.format(target))
            try:
                text = "You got kicked from {} by {} for reason **{}**."
                await target.send(text.format(ctx.guild, ctx.author, reason))
            except Exception as e:
                print(f"[ERROR][Moderation-Kick] {e}")
            try:
                await target.kick(reason=reason)
            except Exception as e:
                print(f"[ERROR][Moderation-Kick] {e}")
                text = "I didn't manage to kick {}, something went wrong!"
                return await ctx.send(text.format(target))
            text = "I kicked {}."
            await ctx.send(text.format(target))

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def ban(self, ctx, target: MemberConverter = None, *, reason=None):
        """Utility|Bans a member.|Ban permission"""

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.message.channel

        if not target:
            text = "I don't know who you want me to ban!"
            return await ctx.send(text)
        if target == ctx.author:
            text = "You shouldn't ban yourself."
            return await ctx.send(text)
        if target.top_role > ctx.author.top_role:
            return await ctx.send("You shouldn't ban your superiors!")
        if target.top_role >= ctx.me.top_role:
            return await ctx.send(f"I can't ban {target} as their role is greater than/equal to my role.")

        if not reason:
            reason = "Unknown"
        text = f"Are you sure you want to ban **{target}**, for reason *{reason}*?\nIf yes, type `confirm`."
        await ctx.send(text)
        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=20)
        except TimeoutError:
            await ctx.send("I'll take this as a no...")
        else:
            if cf_mes.content.lower() != "confirm":
                text = "{} got away from the ban, *for now*."
                return await ctx.send(text.format(target))
            try:
                text = "You got banned from {} by {} for reason **{}**."
                await target.send(text.format(ctx.guild, ctx.message.author, reason))
            except Exception as e:
                print(f"[ERROR][Moderation-Ban] {e}")
            try:
                await target.ban(reason=reason, delete_message_days=3)
            except Exception as e:
                print(f"[ERROR][Moderation-Ban] {e}")
                text = "I didn't manage to ban {}, something went wrong!"
                return await ctx.send(text.format(target))
            text = "I banned {}."
            await ctx.send(text.format(target))

    report = app_commands.Group(name="report", description="Utility|Create or view reports (tickets).|")

    @report.command()
    async def add(self, interaction: discord.Interaction):
        """Utility|Submit feedback via a report (ticket). Details are recorded and sent to Amathy's devs.|"""
        await interaction.response.send_modal(Feedback())

    @report.command()
    @app_commands.describe(report_id="Report ID received on report creation.")
    async def view(self, interaction: discord.Interaction, report_id: int):
        """Utility|View report status and details.|"""
        with db_session:
            report = Report.get(id=int(report_id))

        if report is None:
            await interaction.response.send_message(f"No report found for ID {report_id}", ephemeral=True)
            return

        fields = [
            ("Author", self.bot.get_user(report.author) or f"User<{report_id}>"),
            ("Status", ReportStatus(report.status).name),
            ("Created at", report.created),
            ("Updated at", report.updated),
        ]
        em = Embed().make_emb(title=f"Report #{report_id} | {report.title}", desc=report.description, fields=fields)
        await interaction.response.send_message(embed=em)

    @report.command()
    async def list(self, interaction: discord.Interaction):
        """Utility|View opened report tickets.|"""

        embeds = []
        with db_session:
            reports = select(r for r in Report if orm.raw_sql("r.status = 0"))

            for report in reports:
                fields = [
                    ("Author", self.bot.get_user(report.author) or f"User<{report.id}>"),
                    ("Status", ReportStatus(report.status).name),
                    ("Created at", report.created),
                    ("Updated at", report.updated),
                ]
                em = Embed().make_emb(title=f"Report #{report.id} | {report.title}", desc=report.description,
                                      fields=fields)
                embeds.append(em)

        if not embeds:
            await interaction.response.send_message(f"No reports found.", ephemeral=True)
            return

        await interaction.response.send_message(embed=embeds[0],
                                                view=Paginator(lambda page: [embeds[page - 1]], len(embeds)))

    @report.command()
    async def set(self, interaction: discord.Interaction, report_id: int, status: ReportStatus):
        """Utility|Change a report's status.|Creator perms."""
        perm_chk = await self.bot.is_owner(interaction.user)
        if not perm_chk:
            await interaction.response.send_message("Access denied!")
            return

        with db_session:
            report = Report.get(id=int(report_id))

            if report is None:
                await interaction.response.send_message(f"No report found for ID {report_id}", ephemeral=True)
                return

            report.status = status.value

        text = f"Report status updated to {status.name} for report ID {report.id}."
        user: discord.User = self.bot.get_user(report.author)
        if user is not None:
            await user.send(text)

        await interaction.response.send_message(text, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
