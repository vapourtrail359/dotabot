# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
from _collections import defaultdict
import asyncio
from utils.checks import dev


def on_queue_channel():
    def predicate(ctx):
        try:
            return ctx.channel.id == 675421307852292127
        except:
            pass
    return commands.check(predicate)

class Main(commands.Cog):
    """The description for Main goes here."""

    def __init__(self, bot):
        self.bot = bot
        self.queue = None
        self.closed = True
        self.accepted = []
        self.kick_dict = defaultdict(lambda: set([]))
        self.kick_threshold = 7
        self.owner = None
        self.channelid = 675421307852292127
        self.do_not_delete = []
        self.queue_post = None
        self.accepted_message = None
        self.status_message = None
        self.cancel_wait = False
        self.previous_status = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel == message.guild.get_channel(self.channelid):
            await asyncio.sleep(5)
            if message.id not in self.do_not_delete and not message.pinned:
                try:
                    await message.delete()
                except:
                    print("failed to delete")

    async def update_queue_post(self, ctx):
        q = self.queue
        e = discord.Embed()
        e.colour = discord.Colour.blue()
        e.title = "Queue:"
        i = 0
        for guyid in q:
            guy = ctx.guild.get_member(guyid)
            if guy:
                if i == 0 and self.owner is not None and self.owner.id in self.queue:
                    if self.closed:
                        if self.owner.id in self.accepted:
                            e.add_field(name=f"\u200b \u0009 [✅] [H] {self.owner.display_name}", value="\u200b",
                                        inline=False)
                        else:
                            e.add_field(name=f"\u200b \u0009 [❎] Host: {self.owner.display_name}", value="\u200b",
                                        inline=False)
                    else:
                        e.add_field(name=f"\u200b \u0009 Host: {self.owner.display_name}", value="\u200b", inline=False)
                else:
                    if self.closed:
                        if guyid in self.accepted:
                            e.add_field(name=f"\u200b \u0009 [✅] \u200b \u0009 {guy.display_name}", value="\u200b",
                                        inline=False)
                        else:
                            e.add_field(name=f"\u200b \u0009 [❎] \u200b \u0009 {guy.display_name}", value="\u200b",
                                        inline=False)
                    else:
                        e.add_field(name=f"\u200b \u0009 {i} \u200b \u0009 {guy.display_name}", value="\u200b",
                                    inline=False)
                i += 1

        channel = ctx.guild.get_channel(self.channelid)
        message = await channel.fetch_message(self.queue_post)
        await message.edit(content='', embed=e)

    @on_queue_channel()
    @commands.command()
    async def create(self, ctx, *, password: str = "default"):
        # if "Host" in [r.name for r in ctx.author.roles]:
        if self.queue is None:
            await self.reset(ctx)
            self.closed = False
            self.owner = ctx.author
            self.queue.append(ctx.author.id)
            channel = ctx.guild.get_channel(self.channelid)
            pre_queue_post = await channel.send("Game's password is: " + password)
            self.do_not_delete.append(pre_queue_post.id)
            self.queue_post = await channel.send("Loading...")
            self.queue_post = self.queue_post.id
            self.do_not_delete.append(self.queue_post)
            await self.call_to_join(ctx)
            self.do_not_delete.append(self.status_message.id)
            await self.update_queue_post(ctx)

        else:
            await ctx.send("Queue already exists!")
        # else:
        #     await ctx.send("Only hosts can do this!")

    async def call_to_join(self, ctx):
        txt = "Queue is now open, waiting for more players to join!"
        if self.status_message is None:
            self.status_message = await ctx.send(txt)
        else:
            await self.status_message.edit(content=txt)

    @on_queue_channel()
    @commands.command()
    async def delete(self, ctx):

        if self.owner == ctx.author:
            await self.do_delete(ctx)
        else:
            await ctx.send("Only the queue owner can do this")

    async def do_delete(self, ctx):
        c = ctx.guild.get_channel(self.channelid)
        await self.reset(ctx)
        self.closed = True
        self.queue = None
        await ctx.send("Queue deleted!")

    async def reset(self, ctx):
        self.queue = []
        self.accepted = []
        self.kick_dict = defaultdict(lambda: set([]))
        self.queue_post = None
        self.do_not_delete = []
        c = ctx.guild.get_channel(self.channelid)
        await c.purge(check=lambda x: not x.pinned)

    async def wait_for_accepts(self, ctx):
        await asyncio.sleep(60)
        if not self.cancel_wait:
            if len(self.accepted) != 10:
                await self.status_message.edit(content="One minute has passed! kicking all non acceptors")
                await asyncio.sleep(5)
                for p in self.queue:
                    if p not in self.accepted:
                        self.queue.remove(p)
                        if self.owner is None or p == self.owner.id:
                            await self.update_queue_post(ctx)
                            await self.re_open_queue_if_necessary(ctx)
                            await self.find_new_host(ctx)
                await self.update_queue_post(ctx)
                await self.re_open_queue_if_necessary(ctx)
        else:
            self.cancel_wait = False

    @on_queue_channel()
    @commands.command()
    async def queue(self, ctx):
        if self.queue is not None:
            if len(self.queue) < 10 and not self.closed:
                if ctx.author.id not in self.queue:
                    self.queue.append(ctx.author.id)
                    await  ctx.send(
                        f"{ctx.author.display_name} joined the queue! we now have {10 - len(self.queue)} open spots!")
                    await self.update_queue_post(ctx)
                    if len(self.queue) == 10:
                        self.closed = True
                        await self.call_to_accept(ctx)
                        await self.update_queue_post(ctx)
                else:
                    await ctx.send("You already are in the queue")
            else:
                await ctx.send(ctx.author.mention + " the queue is already closed, sorry!")
        else:
            await ctx.send("There is no queue to join!")

    async def call_to_accept(self, ctx):
        members = [ctx.guild.get_member(id) for id in self.queue if id > 20]
        mentions = [m.mention for m in members]
        await self.status_message.edit(
            content="Queue is now full, please send !accept in this text channel to confirm "
                    "your participation in the match. You have one minute to do this, or you'll be "
                    "kicked! \n" + ' '.join(
                mentions))
        await self.wait_for_accepts(ctx)

    @on_queue_channel()
    @commands.command()
    async def accept(self, ctx):
        if self.closed:
            if ctx.author.id in self.queue:
                if ctx.author.id not in self.accepted:
                    self.accepted.append(ctx.author.id)
                    await  ctx.send(f"{ctx.author.display_name} locked in!")
                    await self.update_queue_post(ctx)
                else:
                    await ctx.send(f"{ctx.author.mention} you already accepted!")
                if len(self.accepted) == 10 == len(self.queue):
                    await self.status_message.edit(content="All players have accepted the match! Let the game start!")
                await self.update_queue_post(ctx)
            else:
                await ctx.send(f"{ctx.author.mention} only people who joined the queue can lock in, sorry!")
        else:
            await ctx.send(f"{ctx.author.mention} the queue is still open, you can't lock in yet!")
    @on_queue_channel()
    @commands.command()
    async def leave(self, ctx):  # name optional

        if ctx.author.id in self.queue:
            if len(self.queue) == 10:
                self.cancel_wait = True
                await self.re_open_queue_if_necessary(ctx)
            self.queue.remove(ctx.author.id)
            await ctx.send(f"{ctx.author.display_name} left the queue")

        if self.closed:
            if ctx.author.id in self.accepted:
                self.accepted.remove(ctx.author.id)
        if ctx.author == self.owner:
            await self.update_queue_post(ctx)
            await self.find_new_host(ctx)
            self.owner = None
        await self.re_open_queue_if_necessary(ctx)
        await self.update_queue_post(ctx)

    @on_queue_channel()
    @commands.command()
    async def kick(self, ctx, *, guy: discord.Member):
        if guy == self.owner:
            await ctx.send("You can't kick the queue owner!")
            return
        if guy.id in self.queue:
            if ctx.author == self.owner:
                await self.do_kick(ctx, guy)
            else:
                self.kick_dict[guy.id].add(ctx.author.id)
                votes = len(self.kick_dict[guy.id])
                await ctx.send(f"{ctx.author.display_name} has voted to kick {guy.display_name}, current vote count: "
                               f"{votes}/{self.kick_threshold}")

                if votes == self.kick_threshold:
                    await self.do_kick(ctx, guy)
            await self.update_queue_post(ctx)
        else:
            await ctx.send(f"{ctx.author.mention} you are not on the queue!")

    async def do_kick(self, ctx, guy):
        await ctx.send(f"{guy.mention} was kicked from the queue!")
        self.queue.remove(guy.id)
        if guy.id in self.accepted:
            self.accepted.remove(guy.id)
        await self.update_queue_post(ctx)
        await self.re_open_queue_if_necessary(ctx)

    async def re_open_queue_if_necessary(self, ctx):
        if len(self.queue) < 10 and self.closed:
            self.accepted = []
            await ctx.send(f"Not enough players to start a game! Re opening the queue to accept new players...")
            await self.call_to_join(ctx)
            self.closed = False
    @dev()
    @commands.command()
    async def test_add(self, ctx, n: int):
        self.queue += list(range(1, 20)[:n])
        await ctx.send(":thumbsup:")
    @dev()
    @commands.command()
    async def test_accept(self, ctx, n: int):
        self.accepted += list(range(1, 20)[:n])
        await ctx.send(":thumbsup:")
    @dev()
    @commands.command()
    async def p(self, ctx):
        await ctx.send(str(self.queue))

    @on_queue_channel()
    @commands.command()
    async def takeover(self, ctx):
        # if "Host" in [r.name for r in ctx.author.roles]:
        if self.owner is None:
            self.owner = ctx.author
            if ctx.author.id not in self.queue:
                self.queue.insert(0, ctx.author.id)
            await  ctx.send(f"{ctx.author.display_name} is the new queue owner!")
            if len(self.queue) == 10:
                self.accepted = []
                await self.call_to_accept(ctx)
            else:
                await self.re_open_queue_if_necessary(ctx)
            await self.update_queue_post(ctx)
        else:
            await ctx.send("This queue already has an owner")
        # else:
        #     await  ctx.send("You are not a host")

    async def find_new_host(self, ctx):
        self.owner = None
        await self.status_message.edit(content="The queue is now owner-less! it will be auto deleted unless a Host "
                                               "uses the !takeover command "
                                               "in the next 2 minutes")
        await asyncio.sleep(2 * 60)
        if self.owner is None:
            await self.status_message.edit(content="No new owner volunteered! deleting queue....")
            await asyncio.sleep(10)
            await self.do_delete(ctx)


def setup(bot):
    bot.add_cog(Main(bot))
