# Overview of BASILEUS
A feature-rich Discord bot made for database management of Discord role-play servers (primarily, but not limited to, the SCP Fandom). At time of writing implements a task assignment systems, database updating and querying, fuzzy searching, NLP-based web scraping, and a permission system.

![Example usage](https://user-images.githubusercontent.com/46630931/185795129-ed91e992-a74a-4f91-abae-105b9613d3ea.png)

# Features
All commands are ran with the prefix set in `config.ini`. Command parameters are labeled with `<>`.

### Submissions cog
Commands primarily focused on the task assignment system of the bot.

* `close`: Must be ran by a Character Helper in a submission review thread. Marks the submission as resolved and the Character Helper as available.

* `ch-available <user_id>`: Forcefully marks a Character Helper as `Available`.

* `ch-unavailable <user_id>`: Forcefully marks a Character Helper as `Unavailable`.

* `ch-hiatus <user_id>`: Forcefully marks a Character Helper as `On Hiatus`.

* `ch-assign <message_id>`: Forcefully assigns a submission to any available Character Helper.

* `add-ch <user_id>:` Adds a Discord user to the Character Helper roster, added as available by default.

* `ch-status`: Outputs the status of every Character Helper.

More commands exist, discoverable by running `help submissions`. They mostly consist of commands that alter a specific field of an object.

### Database cog
Commands primarily associated with the database; covers adding, removing, updating, and searching for  entries.

* `db_show`: Prints a link to the actively used database

* `find_scp <number_or_nick>`: Finds and outputs an object of the SCP-class based off its number or nickname. If a nickname is used the bot attempts a fuzzy search to account for partial input. Utilizes binary search.

* `random_scp`: Outputs a random object of the SCP-class.

* `status <user_id>`: Finds and outputs all objects of the SCP-class that are owned by the target Discord user.

* `excerpt <number> <text>`: Finds an object of the SCP-class corresponding to the number and replaces the object's excerpt field with the inputted text. Note that the command only works if ran by an Administrator or if the user is the owner of the object.

More commands exist, discoverable by running `help database`. They mostly consist of commands that alter a specific field of an object, or add/remove an entire object.

### Misc cog
Background handling of non-critical aspects of the server such as the server clock. 

* `purge`: Kicks all members with the `Inactive` role (as specified in `config.ini`).

# Setup
All information regarding how to setup the `config.ini` file. Once set up, simply run the bot and add it to your server.


### Bot setup

* Go to the Discord Developer Portal and add a new bot.

* Edit the `config.ini` with the new Discord Bot Token.

### Database setup

* Create a Google Spreadsheet with all necessary fields in accordance with the `Database Rows` section of `config.ini`.

* Using Google's API, create a bot account with read and edit access to the spreadsheet.

* Add the spreadsheet ID and the Google API file to `config.ini`.

### Server setup
The bot requires a few roles and channels to work. Edit the `config.ini` with the necessary role/channel IDs.

* `Main Server`: An ID corresponding to that of the assigned server.

* `Character Helper` role: A role given to any server members that are to be assigned submissions to review. 

* `Inactivity` role: A role given to inactive members so that the bot may kick them.

* `Character Helper Hub` channel: A channel where Character Helpers will be assigned to review submissions via in-channel threads.

* `X Subs` channel: Three channels where users may submit their submissions and have them be forwarded to the Character Helpers to review.

* `Clock` channel: A voice channel that is updated every minutes to display the current EST time (accounts for daylight saving).

* `Member Count` channel: A channel that displays the current amount of human members of a server. Updates with every server leave or join.


### Hosting

The bot can be hosted via any traditional Discord bot hosting services, but has been extensively tested with the Heroku platform - the `Procfile` has been written so that it works with Heroku.

### Issues? Please let me know

If you run into any problems or issues while setting up the bot, **please** let me know so we can address and fix them right away. You can report any and all issues via this repository.

# Frequently Asked Questions

**Q: How do reviewers get assigned to submissions?**

Every time a submission is detected in one of the submission channels, the bot marks it. It then checks if there is any available reviewer. If so, the submission's status changes and it gets privately assigned to the available Character Helper (the 'primary reviewer') and a random other Character Helper regardless of their current assignments (the 'secondary reviewer'). If after 24 hours the primary reviewer hasn't closed the submission, a tertiary reviewer is brought in. If after another 24 hours the submission is still open, the entire Character Helper team is brought in to resolve the situation.

**Q: Why is the chosen database Google Sheets instead of something like MySQL?**

There are two reason
Firstly, much of the initial data prior to the bot being developed was already stored in Google Sheets. Secondly and more importantly, one of the limitations of Heroku, where the bot was freely hosted, was that the hosted files cannot be edited. In other words, it wasn't an option to host a traditional database and I instead had to get creative.

**Q: Aren't query responses slow due to using Google Sheets?**

On its own, relatively so. The maximum delay of the original version was around half a second (even with binary search). Still, when multiple people would conduct queries the delay started getting much larger. As such, a variation of the entire database is now consistently kept in-memory (RAM) which has made basic search queries near-instantaneous.

**Q: The `config.ini` is asking for Discord IDs. What are those?**

Every channel, user, and role in Discord has an ID. To be able to view these IDs you'll have to enable Developer mode.
