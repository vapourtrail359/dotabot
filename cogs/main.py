# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
from _collections import defaultdict
import asyncio
from utils.checks import dev

def on_queue_channel():
    def predicate(ctx):

        return (ctx.channel.id == 677266311008616489) or (ctx.guild is None)

    return commands.check(predicate)


class Main(commands.Cog):
    """The description for Main goes here."""

    def __init__(self, bot):
        self.bot = bot
        self.queue = None
        self.closed = True
        self.accepted_ready_check = {}
        self.mentions = []
        self.accepted = []
        self.ready_check_post = None
        self.kick_dict = defaultdict(lambda: set([]))
        self.kick_threshold = 7
        self.owner = None
        self.channelid = 677266311008616489
        self.do_not_delete = []
        self.queue_post = None
        self.accepted_message = None
        self.status_message = None
        self.cancel_wait = False
        self.previous_status = None
        self.pre_queue_post = None
        self.password = None
        self.guild_id = 663479618564653113
        self.guild = bot.get_guild(self.guild_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is not None and message.channel == message.guild.get_channel(self.channelid):
            await asyncio.sleep(5)
            if message.id not in self.do_not_delete and not message.pinned and \
                    (self.status_message is None or not message.id == self.status_message.id) \
                    and (self.pre_queue_post is None or not message.id == self.pre_queue_post.id):
                try:
                    await message.delete()
                except:
                    print("failed to delete")

    def update_guild(self):
        self.guild = self.bot.get_guild(self.guild_id)

    async def update_queue_post(self, ctx):
        q = self.queue
        e = discord.Embed()
        e.colour = discord.Colour.blue()
        e.title = "Queue:"
        i = 0
        self.update_guild()

        if self.owner is not None and self.owner.id in self.queue:
            if self.closed:
                if self.owner.id in self.accepted:
                    e.add_field(name=f"\u200b \u0009 [✅] [H] {self.owner.display_name}", value="\u200b",
                                inline=False)
                else:
                    e.add_field(name=f"\u200b \u0009 [❌] Host: {self.owner.display_name}", value="\u200b",
                                inline=False)
            else:
                e.add_field(name=f"\u200b \u0009 Host: {self.owner.display_name}", value="\u200b", inline=False)

            i += 1

        for guyid in q:
            guy = self.guild.get_member(guyid)
            if guy:
                if guy != self.owner:
                    if self.closed:
                        if guyid in self.accepted:
                            e.add_field(name=f"\u200b \u0009 [✅] \u200b \u0009 {guy.display_name}", value="\u200b",
                                        inline=False)
                        else:
                            e.add_field(name=f"\u200b \u0009 [❌] \u200b \u0009 {guy.display_name}", value="\u200b",
                                        inline=False)
                    else:
                        e.add_field(name=f"\u200b \u0009 {i + 1} \u200b \u0009 {guy.display_name}", value="\u200b",
                                    inline=False)
                    i += 1

        channel = self.guild.get_channel(self.channelid)
        message = await channel.fetch_message(self.queue_post)
        await message.edit(content=f"Open spots: {10 - len(self.queue)}", embed=e)

    async def update_ready_check_post(self, ctx):
        self.update_guild()
        channel = self.guild.get_channel(self.channelid)
        ready_check_post = await channel.fetch_message(self.ready_check_post)
        e = discord.Embed()

        for guyid in self.accepted_ready_check:
            guy = self.guild.get_member(guyid)
            name = guy.display_name

            if self.accepted_ready_check[guyid]:
                e.add_field(name=f"\u200b \u0009 [✅] \u200b \u0009 {guy.display_name}", value="\u200b",
                            inline=False)
            else:
                e.add_field(name=f"\u200b \u0009 [❌] \u200b \u0009 {guy.display_name}", value="\u200b",
                            inline=False)


        await ready_check_post.edit(
            content="A player has requested a ready-check. Please send !accept here or "
            "in dms to confirm you are still ready to play. You have two "
            "minutes to do this, or the ready-check will be unsuccessful.\n" + ' '.join(self.mentions),
            embed=e)
        pass

    @on_queue_channel()
    @commands.command()
    async def host(self, ctx, *, password: str = "dota"):
        if self.queue is None:
            await self._create(ctx, password=password, author_is_owner=True)
            self.password = password
        elif self.owner is None:
            self.owner = ctx.author
            await self.pre_queue_post.edit(content="Game's password is: " + password)
            self.password = password
            await self.update_queue_post(ctx)
            if ctx.author.id not in self.queue:
                self.queue.append(ctx.author.id)
                await self.update_queue_post(ctx)
            await self.update_queue_post(ctx)
            if len(self.queue) == 10:
                self.closed = True
                await self.call_to_accept(ctx)
        else:
            await ctx.send("The current queue already has a host")

        await self.update_queue_post(ctx)

    async def _create(self, ctx, password=None, author_is_owner=False):
        if author_is_owner:
            owner = ctx.author
        else:
            owner = None
        await self.reset(ctx)
        self.closed = False
        self.owner = owner
        self.queue.append(ctx.author.id)
        channel = self.guild.get_channel(self.channelid)
        if password is not None:
            self.pre_queue_post = await channel.send("Game's password is: " + password)
        else:
            self.pre_queue_post = await channel.send("No password yet")
        self.do_not_delete.append(self.pre_queue_post.id)
        self.queue_post = await channel.send("Loading...")
        self.status_message = await ctx.send("...")
        self.queue_post = self.queue_post.id
        self.do_not_delete.append(self.queue_post)
        await self.call_to_join(ctx)
        self.do_not_delete.append(self.status_message.id)
        await self.update_queue_post(ctx)

    async def call_to_join(self, ctx):
        txt = "Queue is now open, waiting for more players to join!"
        await self.update_status(txt)

    async def update_status(self, txt):
        try:
            await self.status_message.edit(content=txt)
        except:
            self.status_message = await ctx.send(txt)
            self.do_not_delete.append(self.status_message.id)

    def is_admin(self, ctx):
        return "Admin" in [r.name for r in ctx.author.roles]

    @on_queue_channel()
    @commands.command()
    async def delete(self, ctx):
        if self.is_admin(ctx):
            await self.do_delete(ctx)
        else:
            await ctx.send("Only the Admins can do this")

    @on_queue_channel()
    @commands.command()
    async def remake(self, ctx, *args):

        if ctx.author.id == self.owner.id:
            visual_queue = self.queue
            visual_queue.remove(self.owner.id)
            visual_queue.insert(0, self.owner.id)
            to_remove = []
            for i in args:
                i = int(i) - 1
                to_remove.append(visual_queue[i])

            for id in to_remove:
                self.queue.remove(id)

            await self.re_open_queue_if_necessary(ctx)
        else:
            await ctx.send("Only the host can do this")

    async def do_delete(self, ctx):
        c = self.guild.get_channel(self.channelid)
        await self.reset(ctx)
        self.closed = True
        self.queue = None
        await ctx.send("Queue deleted!")

    async def reset(self, ctx):
        self.queue = []
        self.accepted = []
        self.accepted_ready_check = {}
        self.mentions = []
        self.kick_dict = defaultdict(lambda: set([]))
        self.queue_post = None
        self.ready_check_post = None
        self.do_not_delete = []
        c = self.guild.get_channel(self.channelid)
        await c.purge(check=lambda x: not x.pinned)

    async def wait_for_accepts(self, ctx):
        self.closed = True
        await self.update_queue_post(ctx)
        await asyncio.sleep(120)
        if not self.cancel_wait:
            if len(self.queue) < 10:
                await self.re_open_queue_if_necessary(ctx)
                return
            elif self.owner is None:
                await self.find_new_host(ctx)
                return
            elif len(self.accepted) != 10:
                await self.update_status("Two minutes has passed! kicking all non acceptors")
                await asyncio.sleep(5)
                self.queue = list(set(self.queue).intersection(set(self.accepted)))
                if self.owner is not None and self.owner.id not in self.queue:  # find new host??
                    self.owner = None
                    await self.pre_queue_post.edit(content="No password yet")

                await self.dm_queue(ctx, f"{10-len(self.queue)} people didn't accept the queue! waiting for more "
                                         f"people...")

                await self.update_queue_post(ctx)
                await self.re_open_queue_if_necessary(ctx)
        else:
            self.cancel_wait = False

    async def wait_for_ready_check_accepts(self, ctx):
        await self.update_ready_check_post(ctx)
        await asyncio.sleep(120)
        if self.is_ready_check_active():
            channel = self.guild.get_channel(self.channelid)
            ready_check_post = await channel.fetch_message(self.ready_check_post)
            not_ready =[self.guild.get_member(id).mention for id in self.accepted_ready_check if not self.accepted_ready_check[id]]
            await ready_check_post.edit(
                content="Ready-check complete, the following players are not ready: " + ' '.join(not_ready),
                embed=None)
            await self.end_ready_check(60)

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
                    if len(self.queue) == 10 and self.owner is not None:
                        self.closed = True
                        await self.end_ready_check(0)
                        await self.call_to_accept(ctx)
                        await self.update_queue_post(ctx)
                    elif self.owner is None:
                        await self.find_new_host(ctx)
                else:
                    await ctx.send("You already are in the queue")
            else:
                await ctx.send(ctx.author.mention + " the queue is already closed, sorry!")
        else:
            await self._create(ctx)

        await self.update_queue_post(ctx)

    async def call_to_accept(self, ctx):
        self.accepted = []
        await self.update_status("Queue is now full, please send !accept here or in dms to confirm "
                                 "your participation in the match. You have two minutes to do this, or you'll be "
                                 "kicked!")

        ping = await self.dm_queue(ctx,
                                   "Queue is now full, please send !accept here or in the queue channel to confirm "
                                   "your participation in the match. You have two minutes to do this, or you'll be "
                                   "kicked!")

        mentions = [m.mention for m in ping]
        await self.update_status("Queue is now full, please send !accept here or in dms to confirm "
                                 "your participation in the match. You have two minutes to do this, or you'll be "
                                 "kicked! \n" + ' '.join(mentions))

        await self.wait_for_accepts(ctx)

    async def dm_queue(self, ctx, txt):
        self.update_guild()
        ping = []
        members = [self.guild.get_member(id) for id in self.queue if id > 20]
        for member in members:
            try:
                await member.send(txt)
            except:
                ping.append(member)
        return ping

    # Accepts a match or ready check
    @on_queue_channel()
    @commands.command()
    async def accept(self, ctx):
        if self.is_ready_check_active():
            if ctx.author.id in self.accepted_ready_check:
                if not self.accepted_ready_check[ctx.author.id]:
                    self.accepted_ready_check[ctx.author.id] = True
                    await ctx.send(f"{ctx.author.mention} is ready!")
                    await self.update_ready_check_post(ctx)
                else:
                    await ctx.send(f"{ctx.author.mention} you already accepted!")

                if all(self.accepted_ready_check):
                    channel = self.guild.get_channel(self.channelid)
                    ready_check_post = await channel.fetch_message(self.ready_check_post)
                    await ready_check_post.edit(content="Ready-check complete, all players are ready!", embed=None)
                    await self.end_ready_check(60)
            else:
                await ctx.send(f"{ctx.author.mention} only people who joined the queue can accept the ready check")
        else:
            await self.update_queue_post(ctx)
            if self.closed:
                if ctx.author.id in self.queue:
                    if ctx.author.id not in self.accepted:
                        self.accepted.append(ctx.author.id)
                        await  ctx.send(f"{ctx.author.display_name} locked in!")
                        await self.update_queue_post(ctx)
                    else:
                        await ctx.send(f"{ctx.author.mention} you already accepted!")
                    if len(self.accepted) == 10 == len(self.queue):
                        self.closed = False
                        await self.update_status("All players have accepted the match! Let the game start!")
                        await self.dm_queue(ctx, "Game has been accepted! password is: " + self.password)
                    await self.update_queue_post(ctx)
                else:
                    await ctx.send(f"{ctx.author.mention} only people who joined the queue can lock in, sorry!")
            else:
                await ctx.send(f"{ctx.author.mention} the queue is still open, you can't lock in yet!")

            await self.update_queue_post(ctx)

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
            await self.pre_queue_post.edit(content="No password yet")
            await self.update_queue_post(ctx)
            await self.find_new_host(ctx)
            self.owner = None
        await self.re_open_queue_if_necessary(ctx)
        await self.update_queue_post(ctx)
        await self.update_queue_post(ctx)

    @on_queue_channel()
    @commands.command()
    async def kick(self, ctx, *, guy: discord.Member):
        if guy == self.owner:
            await ctx.send("You can't kick the queue owner!")
            return
        if guy.id in self.queue:
            if ctx.author == self.owner or self.is_admin():
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
        await self.update_queue_post(ctx)

    async def do_kick(self, ctx, guy):
        await ctx.send(f"{guy.mention} was kicked from the queue!")
        self.queue.remove(guy.id)
        if guy.id in self.accepted:
            self.accepted.remove(guy.id)
        await self.update_queue_post(ctx)
        await self.re_open_queue_if_necessary(ctx)

    async def re_open_queue_if_necessary(self, ctx):
        if len(self.queue) < 10:
            self.accepted = []
            await self.call_to_join(ctx)
            self.closed = False
        elif self.owner is None:
            await self.find_new_host(ctx)

        await self.update_queue_post(ctx)

    @on_queue_channel()
    @commands.command()
    async def readycheck(self, ctx, *args):
        if not self.is_admin(ctx):
            await ctx.send("Only the Admins can do this")
            return

        # Don't send ready checks when the queue is nonexistant/full or when a ready check is in progress
        if not self.queue:
            await ctx.send("There is no queue yet")
            return
        elif self.closed:
            await ctx.send("The queue is already full")
            return
        elif self.is_ready_check_active():
            await ctx.send("A ready check is already in progress")
            return

        self.accepted_ready_check = {id: False for id in self.queue}

        self.ready_check_post = await ctx.send("Loading...")
        self.ready_check_post = self.ready_check_post.id
        self.do_not_delete.append(self.ready_check_post)

        ping = await self.dm_queue(ctx,
                                   "A player has requested a ready-check. Please send !accept here or in the queue "
                                   "channel to confirm you are still ready to play. You have two minutes to do "
                                   "this, or the ready-check will be unsuccessful."
                                   )

        mentions = [m.mention for m in ping]

        self.ready_check_mentions = mentions
        await self.update_ready_check_post(ctx)

        await self.wait_for_ready_check_accepts(ctx)

    def is_ready_check_active(self):
        return len(self.accepted_ready_check) > 0

    async def end_ready_check(self, post_delete_delay):
        self.accepted_ready_check = {}
        self.mentions = []
        ready_check_post_id = self.ready_check_post
        channel = self.guild.get_channel(self.channelid)
        ready_check_post = await channel.fetch_message(ready_check_post_id)
        await asyncio.sleep(post_delete_delay)
        if ready_check_post_id in self.do_not_delete:
            self.do_not_delete.remove(ready_check_post_id)
        try:
            await ready_check_post.delete()
        except:
            print("Failed to delete")
        self.ready_check_post = None

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

    # @on_queue_channel()
    # @commands.command()
    # async def takeover(self, ctx):
    #     # if "Host" in [r.name for r in ctx.author.roles]:
    #     if self.owner is None:
    #         self.owner = ctx.author
    #         if ctx.author.id not in self.queue:
    #             self.queue.insert(0, ctx.author.id)
    #         await  ctx.send(f"{ctx.author.display_name} is the new queue owner!")
    #         if len(self.queue) == 10:
    #             self.accepted = []
    #             await self.call_to_accept(ctx)
    #         else:
    #             await self.re_open_queue_if_necessary(ctx)
    #         await self.update_queue_post(ctx)
    #     else:
    #         await ctx.send("This queue already has an owner")
    # else:
    #     await  ctx.send("You are not a host")

    async def find_new_host(self, ctx):
        self.owner = None
        if len(self.queue) == 10:
            await self.update_status("Waiting for a host to volunteer! (`!host <password>)`")
        else:
            await self.re_open_queue_if_necessary(ctx)


def setup(bot):
    bot.add_cog(Main(bot))
