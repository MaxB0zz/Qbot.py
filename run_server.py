import os

import discord
from discord import app_commands, ButtonStyle
from discord.ext import tasks
import time
from datetime import datetime
from pysondb import db
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TOKEN")
guild_id = os.getenv("GUILD_ID")
channel_id = os.getenv("CHANNEL_ID")

dbase = db.getDb("data.json")


class bot_client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False
        self.index = 0

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=guild_id))  # we can remove the id later for general uses
            self.synced = True
        print(f"Connected! \n")
        app_loop.start()

    async def on_message(self, message):
        if message.content.startswith('hey'):
            msg = await message.channel.send('I will delete myself now...')
            await msg.delete()


client = bot_client()
tree = app_commands.CommandTree(client)


@tasks.loop(seconds=5.0)
async def app_loop():
    channel = client.get_channel(int(channel_id))
    allTasks = dbase.getAll()
    toNotify = []
    for task in allTasks:
        diff = datetime.fromtimestamp(task.get("date")) - datetime.now()
        if diff.days < 0:
            dbase.deleteById(task.get("id"))
        elif diff.days <= 1 and bool(task.get("isNotified")) is False:
            toNotify.append(task)
            dbase.updateById(task.get("id"), {"isNotified": True})
    if len(toNotify) > 0:
        embed = discord.Embed(title="Upcoming Tasks!", description="Watch out! these tasks are expiring tomorrow",
                              color=0x72d345)
        embed.set_footer(text=":)")
        for task in toNotify:
            date = datetime.fromtimestamp(task.get("date")).strftime('%d-%m-%y')
            embed.add_field(name=date + ":   [id: " + str(task.get("id")) + "]",
                            value="\t\t\t" + task.get("desc") + "\n")
        await channel.send(embed=embed)


def create_embed_tasks():
    def takeFirst(elem):
        return elem.get("date")

    allTasks = dbase.getAll()
    allTasks.sort(key=takeFirst)

    embed = discord.Embed(title="Ongoing Tasks", description="Underneath, the list of the currently active tasks!\n\t\t",
                          color=0x72d345)
    embed.set_thumbnail(url="https://imgs.search.brave.com/7xNl_XxofOQ423X7Od6g2pEpe5XkuLZiGp5T8ITb3HM/rs:fit:1200"
                            ":1200:1/g:ce/aHR0cDovL2NsaXBh/cnQtbGlicmFyeS5j/b20vaW1hZ2VfZ2Fs/bGVyeS9uMTM2ODMy/NS5wbmc")
    embed.set_footer(text="today: " + datetime.now().strftime('%d-%m-%y'))
    if len(allTasks) == 0:
        embed.add_field(name="No active tasks yet...", value="/addtask in order to create a new task!")
    for task in allTasks:
        date = datetime.fromtimestamp(task.get("date")).strftime('%d-%m-%y')
        embed.add_field(name=date + ":   [id: " + str(task.get("id")) + "]",
                        value="\t\t\t" + task.get("desc") + "\n")
    return embed, len(allTasks)


class DeleteButton(discord.ui.Button):
    def __init__(self, selected):
        self.selected_id = selected
        super().__init__(label="delete task", style=ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        if len(self.selected_id) == 0:
            await interaction.response.send_message("Oi, you haven't selected any tasks to delete you dumb ass", ephemeral=True, delete_after=3)
        else:
            try:
                dbase.deleteById(self.view.DeleteButton.selected_id)

                embed, size = create_embed_tasks()
                if size == 0:
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    view = DropdownView()
                    await interaction.response.edit_message(
                        embed=embed, view=view)


            except:
                await interaction.response.send_message("oh no! something went wront and we couldn't delete your task :(, try again!",
                                                        ephemeral=True, delete_after=5)


class Dropdown(discord.ui.Select):
    def __init__(self):
        allTasks = dbase.getAll()
        options = []

        for task in allTasks:
            options.append(discord.SelectOption(label=str(task.get("id")), description=task.get("desc")))

        super().__init__(placeholder='Select your target task', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.DeleteButton.selected_id = self.values[0]
        await interaction.response.defer()


class DropdownView(discord.ui.View):

    def __init__(self):
        super().__init__()

        self.drop = Dropdown()
        self.DeleteButton = DeleteButton(self.drop.values)
        # Adds the dropdown to our view object.
        self.add_item(self.drop)
        self.add_item(self.DeleteButton)



@tree.command(name="addtask", description="add a new task to your list", guild=discord.Object(id=guild_id))
async def add_task(interaction, date: str, desc: str):
    try:
        date = time.mktime(datetime.strptime(date, "%d/%m/%Y").timetuple())
    except ValueError:
        await interaction.response.send_message("Your date is not valid :(")
        return
    todayTs = time.time()
    if todayTs > date:
        await interaction.response.send_message("Your Task cannot be scheduled in the past wtf")
        return
    if len(desc) == 0:
        await interaction.response.send_message("Your Task cannot be empty you silly goose")
        return

    dbase.add({"date": date, "desc": desc, "isNotified": False})

    await interaction.response.send_message("task successfully added!")


@tree.command(name="tasks", description="see the current tasks", guild=discord.Object(id=guild_id))
async def get_tasks(interaction):
    embed, size = create_embed_tasks()
    if size == 0:
        await interaction.response.send_message(embed=embed)
    else:
        view = DropdownView()
        await interaction.response.send_message(
            embed=embed, view=view)


@tree.command(name="cleartasks", description="clear all tasks", guild=discord.Object(id=guild_id))
async def clear_tasks(interaction):
    dbase.deleteAll()
    await interaction.response.send_message("Tasks list cleared!")


@tree.command(name="deletetask", description="delete one task", guild=discord.Object(id=guild_id))
async def clear_tasks(interaction, task_id: int):
    try:
        dbase.deleteById(task_id)
    except:
        await interaction.response.send_message("Id " + str(task_id) + " does not exist you goof")
        return
    await interaction.response.send_message("Tasks successfully deleted!")


client.run(token)
