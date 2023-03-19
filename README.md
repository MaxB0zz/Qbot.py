# Qbot.py

A very simple discord bot to manage tasks! 

in order to use it you need to install:

`pip install discord.py`
`pip install pysondb`
`pip install python-dotenv`

create an `.env` file next to your bot with the follow credentials:

TOKEN | 
GUILD_ID | 
CHANNEL_ID

and then just run:

`python run_server.py`

## Avaible Commands so far:

`/addtask [dd/mm/yyyy] [description]` *add a new task to your task list*
`/tasks` *get an embed list of your ongoing messages (possibility to delete one task of the list*
`/deletetask [id]` *delete the corresponding task*
 `/cleartasks` *delete all ongoing tasks*
 
 additionnaly, every outdated task is automatically deleted from the database. Furthermore, the bot warns the users of a task's deadline a day before the deadline
 
 more features are coming soon!
 
 :)
