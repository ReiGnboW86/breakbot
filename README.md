# BreakBot #
A simple discord bot to manage breaks in class or during tasks

This focuses on helping teachers mainly to manage large groups of people to send information about breaks over discord.

This is a discord bot that manages breaks in our class and keeps track of previous break times and also shows it in a neat way.

My first real project since starting my education, hope it will come of use for many after I'm satisfied with the result.

USAGE MANUAL

1. Create at text channel in your discord server named breakbot.
2. Edit which user should have permission to control the bot in the code of 'breakbot.py' on line 19
3. Invite the bot to your discord server and place it in the channel breakbot.
4. The user with permission has access to these commands:

# FUTURE COMMANDS

# !start #

Starts a countdown for a break. The # specifies how long the break should last.
The bot will send a message saying when the break starts and how long it will last, and will send warnings when there are 2 minutes and 30 seconds remaining.

Example: !start 5 starts a 5-minute break.

# !stop

Stops the current break timer.
This command allows you to cancel the break and send a message that the break was stopped after x time.

Example: !stop


# !last

Displays information about the last break taken, such as how long the break lasted and when it ended.

Example: !last




