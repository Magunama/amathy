from discord.ext import commands
from utils.embed import Embed


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_categories = ["music", "media", "utility", "fun", "info", "explicit"]

    async def send_help(self, cmd):
        subcmds = []
        if hasattr(cmd, "commands"):
            subcmds = cmd.commands
        title = f"[Amathy v1.8] - Help - {cmd.name} | " + " | ".join(cmd.aliases)
        help_str = cmd.help
        desc = req = cat = "N/A"
        if help_str:
            if "|" in help_str:
                cat, desc, req = help_str.split("|")
        desc = f"You have accessed the instruction manual.\nBelow are details about the `{cmd.name}` command.\n\n**[Category]**: {cat}\n**[Description]**: {desc}\n**[Requirements]**: {req}"
        fields = []
        for cmd in subcmds:
            help_str = cmd.help.split("|")[1]
            fields.append([cmd.name, help_str, False])
        footer = "1/1 - This is all I can tell you. ^^ I don't know anything more than this."
        return Embed().make_emb(title, desc, None, fields, footer)

    async def main_page(self, ctx):
        website = "https://amathy.moe"
        supp_server = "https://discord.gg/D87ykxd"
        vote = "https://discordbots.org/bot/410488336344547338/vote"
        invite = self.bot.invite_link
        links = f"\n[Website!]({website}) ✤ [Support server!]({supp_server}) ✤ [Vote me & get rewards!]({vote}) ✤ [Invite me!]({invite})\n"
        emb_text = "Do you need my instruction manual?\n** ▶ Available prefixes**: default: {}; custom: `Unavailable`\n**▶ Useful links**:{}**▶ Below are the corresponding categories to my commands**:"
        emb_cat = "Music, yay|Reactions + others|Help the server|Just for fun|For information|Not for everyone".split("|")
        title = "[Amathy v1.8] - Help - Main Page"  # todo: some dynamic versioning?
        pref_string = []
        for pref in ctx.bot.prefixes:
            pref_string .append(f"`{pref}`")
        pref_string = ", ".join(pref_string)
        desc = emb_text.format(pref_string, links)
        fields = []
        for i in range(0, 6):
            fields.append([self.help_categories[i].title(), emb_cat[i], True])
        footer = "1/1 - To see details about a certain category, use ama help [category]."
        embed = Embed().make_emb(title, desc, None, fields, footer)
        await ctx.send(embed=embed)

    async def cat_page(self, ctx, cat):
        showlist = []
        for c in ctx.bot.commands:
            help_str = c.help
            if help_str:
                if "|" in help_str:
                    c_cat = help_str.split("|")[0]
                    if c_cat.lower() == cat.lower():
                        showlist.append([c.name, " | ".join(c.aliases), True])
        showlen = len(showlist)
        if showlen % 10 == 0:
            lastpage = int(showlen / 10)
        else:
            lastpage = int(showlen / 10) + 1
        showlist.sort()
        title = f"[Amathy v1.8] - Help - {cat.title()} category page"
        desc = f"You have accessed the instruction manual.\nBelow are commands from the `{cat.title()}` category."
        if not showlist:
            footer = "1/1 - To see more details about a command, use ama help [command]."
            emb = Embed().make_emb(title, desc, footer=footer)
            return await ctx.send(embed=emb)
        embeds = []
        for i in range(1, lastpage + 1):
            fields = []
            for j in range((i - 1) * 10, (i * 10) - 1):
                if not j < showlen:
                    break
                fields.append(showlist[j])
            footer = "{}/{} - To see more details about a command, use ama help [command].".format(i, lastpage)
            embed = Embed().make_emb(title, desc, None, fields, footer, empty_field=True)
            embeds.append(embed)
        await self.bot.funx.embed_menu(ctx, embeds)

    async def cmd_page(self, ctx, cmd):
        for c in ctx.bot.commands:
            if cmd == c.name or cmd in c.aliases:
                emb = await self.send_help(c)
                await ctx.send(embed=emb)
                return True
        return False

    async def err_page(self, ctx):
        title = "[Amathy v1.8] - Help - Page not found"
        desc = "You have accessed the instruction manual.\nIt seems that you haven't selected an existing command. :("
        footer = "1/1 - The selected command doesn't exist. Use ama help if you got lost."
        embed = Embed().make_emb(title, desc, footer=footer)
        await ctx.send(embed=embed)

    @commands.command(aliases=["h"])
    async def help(self, ctx, args=None):
        """Info|Shows the help page.|"""
        if not args:
            return await self.main_page(ctx)
        else:
            args = args.lower()
            if args in self.help_categories:
                return await self.cat_page(ctx, args)
            found = await self.cmd_page(ctx, args)
            if not found:
                await self.err_page(ctx)


def setup(bot):
    bot.add_cog(Help(bot))
