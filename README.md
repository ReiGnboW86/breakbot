# BreakBot #

A simple discord bot to manage breaks in class or during tasks

This focuses on helping teachers or bosses mainly to manage larger groups of people to send information about breaks over discord.

This is a discord bot that manages breaks in class and keeps track of previous break times and also shows it in a neat way.

My first real project since starting my education, hope it will come of use for many after I'm satisfied with the result.

USAGE / INSTALLATION MANUAL

Invite Link:

https://discord.com/oauth2/authorize?client_id=1286591728865775646

# Bugs

None I've found atm (please report if you find any)

# COMMANDS (implemented)

# !start HH:MM

Starts a countdown for a break. The # specifies how long the break should last.
The bot will send a message saying when the break starts and how long it will last, and will send warnings when there are 2 minutes and 30 seconds remaining.

Example: !start 14:20 Starts a break that will end @ 14:20 and displays a timer counting down and approximate time in minutes of the break.

# !stop

Stops the current break timer.
This command allows you to cancel the break and send a message that the break was stopped after x time.

Example: !stop


# !last

Displays information about the last break taken, such as how long the break lasted and when it ended.

Example: !last

# !how

Displays all the commands available to the user, including this command.

Example : !how

# !settimezone

Sets the timezone to whatever timezone you want the bot to operate in, and stores it for future use.

Example: !settimezone Europe/Stockholm

# !promote @username

Sets the targeted user to be a Supreme Break Commander, giving them the rights to use the !start, !stop and !settimezone commands.

Example: !promote @Amanda

# !demote @username

Removes the targeted user from its role as a Supreme Break Commander, demoting them to a regular human being again.

# !role

Displays some fun information about which your role in the breakbot world is.

Example: !role

# Latest Updates

Added the !promote @username & !demote @username command to be able to assign Break Operators other than the admin
Added a fun little !role message to check which role you have

# Current thoughts

Ask for input from the user if the break is over 30 minutes to confirm its a lunch break or not, otherwise default to normal break

Add the possibility to choose between a task or a break when starting a timer (taskbot?!)

Add some fun emojis to the messages to make it look more playful

Fix so that the bot doesn't require admin priviliges (Next Week perhaps)

If you have any suggestions for functionality you would like to see, Please send me a message :)