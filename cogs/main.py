from discord.ext import commands
import psutil
import platform
from utils.embed import Embed


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_size(bytes, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    @commands.command(aliases=["sys"])
    async def system(self, ctx):
        """Info|Shows system resources.|"""
        # todo: add cooldown
        fields = []

        # System information
        uname = platform.uname()
        fields.append(["System", uname.system, True])
        fields.append(["Version", uname.version, True])

        # CPU Info
        fields.append(["Physical cores:", psutil.cpu_count(logical=False), True])
        # CPU frequencies
        cpufreq = psutil.cpu_freq()
        fields.append(["Frequency:", f"{cpufreq.current:.2f}Mhz", True])
        # CPU usage
        fields.append(["CPU usage:", f"{psutil.cpu_percent()}%", True])

        # Memory Information
        svmem = psutil.virtual_memory()
        fields.append(["Total memory", self.get_size(svmem.total), True])
        fields.append(["Available memory", self.get_size(svmem.available), True])
        fields.append(["Used memory", self.get_size(svmem.used), True])
        fields.append(["Memory percentage", f"{svmem.percent}%", True])

        # My processes
        ret = 0
        for proc in psutil.process_iter():
            if proc.name() in ["python3", "python3.exe", "java", "java.exe", "mysqld", "mysqld.exe"]:
                ret = ret + proc.memory_info().rss
        footer = f"Amathy's memory consumption:  {self.get_size(ret)}"

        title = ctx.command.qualified_name
        author = {"name": ctx.bot.user.name, "icon_url": ctx.bot.user.avatar_url}
        desc = "Here are some details about system resources."
        await ctx.send(embed=Embed().make_emb(title, desc, author, fields, footer))


def setup(bot):
    bot.add_cog(Main(bot))
