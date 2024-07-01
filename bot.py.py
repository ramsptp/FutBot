import discord
from discord.ext import commands, tasks
from rapidfuzz import process
import sqlite3
import random
import asyncio
import logging
from fuzzywuzzy import process

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('cards_game.db')
cursor = conn.cursor()




#---------------------------------------------------------TABLES-------------------------------------------------------------------------------------
# Create tables (if not already created)
cursor.execute('''
CREATE TABLE IF NOT EXISTS cards (
    card_id INTEGER PRIMARY KEY,
    player_id TEXT,
    name TEXT,
    attack INTEGER,
    defense INTEGER,
    speed INTEGER,
    height TEXT,
    club TEXT,
    position TEXT,
    overall INTEGER,
    image_path TEXT,
    card_rarity TEXT,
    card_type TEXT,
    league TEXT,
    nation TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS decks (
    user_id INTEGER,
    deck_name TEXT,
    cards TEXT,
    FOREIGN KEY(user_id) REFERENCES players(user_id)
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    battles_played INTEGER DEFAULT 0,
    battles_won INTEGER DEFAULT 0,
    battles_lost INTEGER DEFAULT 0,
    has_claimed_starter_pack BOOLEAN DEFAULT 0,
    rounds_played INTEGER DEFAULT 0,
    rounds_won INTEGER DEFAULT 0,
    rounds_lost INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS inventories (
    user_id INTEGER,
    card_id INTEGER,
    edition INTEGER,
    FOREIGN KEY(user_id) REFERENCES players(user_id),
    FOREIGN KEY(card_id) REFERENCES cards(card_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS achievements (
   	achievement_id	INTEGER,
	title	TEXT NOT NULL,
	description	TEXT NOT NULL,
	PRIMARY KEY(achievement_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_achievements (
    	user_id	INTEGER,
	achievement_id	INTEGER,
	date_earned 	DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(user_id,achievement_id),
	FOREIGN KEY(user_id) REFERENCES players(user_id),
	FOREIGN KEY(achievement_id) REFERENCES achievements(achievement_id)
)
''')



#---------------------------------------------------------SETUP-------------------------------------------------------------------------------------

conn.commit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['!'], intents=intents)

allowed_channels = [1255230565875978240, 1255360547105542186]
                    
@bot.event
async def on_message(message):
    if message.channel.id in allowed_channels:
        await bot.process_commands(message)





#---------------------------------------------------------HELP-------------------------------------------------------------------------------------

bot.remove_command('help')

class HelpMenu(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.current_page = 0
        self.total_pages = len(embeds)
        self.update_buttons()

    def update_view(self):
        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")
        return embed

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.total_pages - 1:
            self.add_item(NextButton())

class PreviousButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Previous', style=discord.ButtonStyle.primary, custom_id='previous')

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page > 0:
            view.current_page -= 1
            embed = view.update_view()
            view.update_buttons()
            await interaction.response.edit_message(embed=embed, view=view)

class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Next', style=discord.ButtonStyle.primary, custom_id='next')

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page < view.total_pages - 1:
            view.current_page += 1
            embed = view.update_view()
            view.update_buttons()
            await interaction.response.edit_message(embed=embed, view=view)


@bot.command(name='help')
async def help_command(ctx):
    view_commands = [
        {"name": "view player_name", "value": "Lets you view advanced details of any card"},
        {"name": "view_deck name", "value": "Displays all the cards in a deck"},
        {"name": "weight player_name", "value": "Displays the pack weight of the card in a standard drop or daily pack."},
        {"name": "inventory", "value": "Displays all the cards you own"},
        {"name": "titles", "value": "Displays every achievement."},
        {"name": "titles @user", "value": "Displays every achievement earned by the user."}
    ]

    battle_commands = [
        {"name": "battle @user", "value": "Initiates a battle between you and the user"},
        {"name": "battle_logic", "value": "Shows how battle works."},
        {"name": "create_deck deck_name card_id1  card_id2  card_id3  card_id4  card_id5", "value": "Creates a deck with 5 cards for battle"},

    ]

    reward_commands = [
        {"name": "daily", "value": "Lets you claim a random card. Cooldown: 24 hours"},
        {"name": "drop", "value": "Lets you claim a random card. Cooldown: 30 minutes"},
        {"name": "get_starter_pack", "value": "Lets you claim 10 players, 6 rated 70-79, 3 rated 80-85, 1 rated 85+"}
    ]

    misc_commands = [
        {"name": "trade yourcard_id @user theircard_id", "value": "Lets you trade one of your cards for one of theirs"},
        {"name": "facts", "value": "Sends a random football fact."},
        {"name": "Secret Commands", "value": "Their are a lot of secret commands related to football hidden throughout. Find them for heavy rewards. PS:They are all lower case and has no special characters."},
        {"name": "suggest", "value": "Sends suggestions to developers."}
    ]

    stat_commands = [
         {"name": "stats", "value": "Shows your stats as a player"},
         {"name": "set_title", "value": "Choose title to display in your !stats"}  
    ]

    leaderboard_commands = [
         {"name": "lb", "value": "Shows players in order of battles wons"},
         {"name": "lb bp", "value": "Shows players in order of battles played"},
         {"name": "lb rw", "value": "Shows players in order of rounds wom"},
         {"name": "lb rp", "value": "Shows players in order of rounds played"}
    ]


    categories = {
        "View Commands": view_commands,
        "Battle Commands": battle_commands,
        "Reward Commands": reward_commands,
        "Miscellaneous Commands": misc_commands,
        "Statistic Commands": stat_commands,
        "Leaderboard Commands": leaderboard_commands
    }

    embeds = []
    for category, commands in categories.items():
        embed = discord.Embed(title=f"{category}", description=f"{category} you can use:", color=0x00ff00)
        for command in commands:
            embed.add_field(name=command["name"], value=command["value"], inline=False)
        embeds.append(embed)

    view = HelpMenu(embeds)
    await ctx.send(embed=embeds[0], view=view)


@bot.command(name='battle_logic')
async def battle_logic(ctx):
    embed = discord.Embed(
        title="Battle Logic",
        description=(
            "Here's how the battle works:\n\n"
            "First both players need to create a deck using create_deck command. After using !battle command, both players have to choose a deck to play with.\n"
            "1. **Card Selection**: Each player selects a card from their deck.\n"
            "2. **Actions**: Players choose their action for the round (Attack, Defense, or Speed).\n"
            "3. **Comparison**: The chosen actions and card stats are compared:\n"
            "   - **Attack vs Defense**: The player's attack is compared to the opponent's defense.\n"
            "   - **Defense vs Attack**: The player's defense is compared to the opponent's attack.\n"
            "   - **Speed vs Speed**: The player's speed is compared to the opponent's speed.\n"
            "4. **Round Outcome**: The winner of the round is determined based on the comparisons:\n"
            "   - Higher stat wins the round.\n"
            "   - If the stats are equal, the round is a draw.\n"
            "5. **Victory**: The first player to win a set number of rounds (e.g., 3 out of 5) wins the battle.\n\n"
            "Good luck and have fun battling!"
        ),
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed)

#---------------------------------------------------------ABOUT-------------------------------------------------------------------------------------


# Bot version and creator information
BOT_VERSION = "1.0.0"
CREATOR = "noobmaster"
DESCRIPTION = "This bot is designed to give maximum resemblance to Match Attax card games. With this bot, you can collect football player cards and battle with your friends using your favourite players."
CHANGELOG = ["1.0.0 - Initial realease"]
# Existing commands like !daily, !drop, !view, etc.

@bot.command(name='about')
async def about(ctx):
    embed = discord.Embed(title="About This Bot", color=discord.Color.blue())
    embed.add_field(name="Version", value=f"```{BOT_VERSION}```", inline=True)
    embed.add_field(name="Creator", value=CREATOR, inline=True)
    embed.add_field(name="Description", value=DESCRIPTION, inline=False)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)


@bot.command(name='version')
async def version(ctx):
    embed = discord.Embed(title="Bot Version")
    embed.add_field(name="Version", value=f"```{BOT_VERSION}```", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='changelog')
async def changelog(ctx):
    embed = discord.Embed(title="Changelog")
    changelog_text = "\n".join([f"```{entry}```" for entry in CHANGELOG])
    embed.add_field(name="Changes", value=changelog_text, inline=False)
    await ctx.send(embed=embed)


#---------------------------------------------------------SUGGESTIONS-------------------------------------------------------------------------------------


@bot.command(name='suggest')
async def suggest(ctx, *, suggestion: str):
    suggestion_channel_id = 1255360547105542186  # Replace with your channel ID
    suggestion_channel = bot.get_channel(suggestion_channel_id)
    if suggestion_channel:
        embed = discord.Embed(title="New Suggestion", description=suggestion, color=0x0000ff)
        embed.add_field(name="Suggested by", value=ctx.author.mention, inline=False)
        await suggestion_channel.send(embed=embed)
        await ctx.send("Thank you for your suggestion! It has been forwarded to the team.")
    else:
        await ctx.send("Sorry, I couldn't find the suggestion channel. Please try again later.")



#---------------------------------------------------------ACHIEVEMENTS-------------------------------------------------------------------------------------

@bot.command(name='titles')
async def display_achievements(ctx, member: discord.Member = None):
    if member is None:
        cursor.execute('SELECT title, description FROM achievements')
        achievements = cursor.fetchall()
        embed = discord.Embed(title="All Achievements", description="List of all possible achievements.")
        for title, description in achievements:
            embed.add_field(name=title, value=description, inline=False)
    else:
        cursor.execute('''
        SELECT a.title, a.description FROM achievements a
        JOIN user_achievements ua ON a.achievement_id = ua.achievement_id
        WHERE ua.user_id = ?
        ''', (member.id,))
        user_achievements = cursor.fetchall()

        if not user_achievements:
            embed = discord.Embed(title=f"{member.name}'s Achievements", description="This user doesn't have any achievements.")
        else:
            embed = discord.Embed(title=f"{member.name}'s Achievements", description="List of achievements earned by the user.")
            for title, description in user_achievements:
                embed.add_field(name=title, value=description, inline=False)
    
    await ctx.send(embed=embed)

        


def determine_card_rarity(overall):
    if overall is None:
        return 'Common'
    if overall > 85:
        return 'Rare'
    elif overall > 75:
        return 'Uncommon'
    else:
        return 'Common'

from discord.ext import commands
from discord.ui import View

def increment_cards_dropped(user_id):
    try:
        conn = sqlite3.connect('cards_game.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET cards_dropped = cards_dropped + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error incrementing cards_dropped: {e}")
    finally:
        conn.close()



#---------------------------------------------------------SECRET COMMANDS-------------------------------------------------------------------------------------

def secret_command():
    def decorator(func):
        async def wrapper(ctx, *args, **kwargs):
            await func(ctx, *args, **kwargs)
            await ctx.message.delete()
        return wrapper
    return decorator


def get_card_by_id(card_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Card(*row)
    return None


#-----------------ENGLAND

itscominghome_card_ids = [10392, 10397, 10406, 10407, 10408, 10411, 10412, 10418, 10428, 10443, 10451, 10453, 10457]

@bot.command(name='itscominghome')
@secret_command()
async def itscominghome(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT itscominghome FROM players WHERE user_id = ?', (ctx.author.id,))
    used_command = cursor.fetchone()[0]

    if used_command:
        await ctx.author.send("You have already used this command.")
        return
    
    card_id = None
    attempts = 0
    max_attempts = len(itscominghome_card_ids) * 2  # To prevent potential infinite loops
    
    while attempts < max_attempts:
        attempts += 1
        card_id = random.choice(itscominghome_card_ids)
        cursor.execute('SELECT 1 FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card_id))
        if cursor.fetchone() is None:
            break

    if card_id is None:
        await ctx.author.send("No available cards to add to your inventory.")
        conn.close()
        return

    card = get_card_by_id(card_id)
    if card:
        card.copies += 1
        add_card(card)
        add_card_to_inventory(ctx.author.id, card.card_id)

        cursor.execute('UPDATE players SET itscominghome = 1 WHERE user_id = ?', (ctx.author.id,))
        conn.commit()
        
        embed = discord.Embed(title="Special Drop", description="You have received a special card drop! Shh, don't tell anyone about this command.")
        embed.add_field(name="Name", value=card.name, inline=True)
        embed.add_field(name="ID", value=card.card_id, inline=True)
        embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
        embed.add_field(name="Type", value=card.card_type, inline=True)
        embed.add_field(name="Attack", value=card.attack, inline=True)
        embed.add_field(name="Defense", value=card.defense, inline=True)
        embed.add_field(name="Speed", value=card.speed, inline=True)
        embed.add_field(name="Overall", value=card.overall, inline=True)
        embed.add_field(name="League", value=card.league, inline=True)
        embed.add_field(name="Nation", value=card.nation, inline=True)
        embed.add_field(name="Copies", value=card.copies, inline=True)
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.author.send(embed=embed, file=discord.File(card.image_path))
        logger.info(f'{ctx.author.name} received a special card {card.name} (ID: {card.card_id}) using !itscominghome')
    else:
        await ctx.author.send("An error occurred while processing your request.")
    
    conn.close()


#----------------------BRAZIL

jogabonito_card_ids = [10394, 10395, 10399, 10405, 10446, 10462, 10465, 10469]

@bot.command(name='jogabonito')
@secret_command()
async def jogabonito(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT jogabonito FROM players WHERE user_id = ?', (ctx.author.id,))
    used_command = cursor.fetchone()[0]

    if used_command:
        await ctx.author.send("You have already used this command.")
        return
    
    card_id = None
    attempts = 0
    max_attempts = len(jogabonito_card_ids) * 2  # To prevent potential infinite loops
    
    while attempts < max_attempts:
        attempts += 1
        card_id = random.choice(jogabonito_card_ids)
        cursor.execute('SELECT 1 FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card_id))
        if cursor.fetchone() is None:
            break

    if card_id is None:
        await ctx.author.send("No available cards to add to your inventory.")
        conn.close()
        return

    card = get_card_by_id(card_id)
    if card:
        card.copies += 1
        add_card(card)
        add_card_to_inventory(ctx.author.id, card.card_id)

        cursor.execute('UPDATE players SET jogabonito = 1 WHERE user_id = ?', (ctx.author.id,))
        conn.commit()
        
        embed = discord.Embed(title="Special Drop", description="You have received a special card drop! Shh, don't tell anyone about this command.")
        embed.add_field(name="Name", value=card.name, inline=True)
        embed.add_field(name="ID", value=card.card_id, inline=True)
        embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
        embed.add_field(name="Type", value=card.card_type, inline=True)
        embed.add_field(name="Attack", value=card.attack, inline=True)
        embed.add_field(name="Defense", value=card.defense, inline=True)
        embed.add_field(name="Speed", value=card.speed, inline=True)
        embed.add_field(name="Overall", value=card.overall, inline=True)
        embed.add_field(name="League", value=card.league, inline=True)
        embed.add_field(name="Nation", value=card.nation, inline=True)
        embed.add_field(name="Copies", value=card.copies, inline=True)
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.author.send(embed=embed, file=discord.File(card.image_path))
        logger.info(f'{ctx.author.name} received a special card {card.name} (ID: {card.card_id}) using !jogabonito')
    else:
        await ctx.author.send("An error occurred while processing your request.")
    
    conn.close()


#--------------------ITALY

pineappleonpizza_card_ids = [10391, 10393, 10414, 10415, 10430, 10455, 10459, 10460]

@bot.command(name='pineappleonpizza')
@secret_command()
async def pineappleonpizza(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT pineappleonpizza FROM players WHERE user_id = ?', (ctx.author.id,))
    used_command = cursor.fetchone()[0]

    if used_command:
        await ctx.author.send("You have already used this command.")
        return
    
    card_id = None
    attempts = 0
    max_attempts = len(pineappleonpizza_card_ids) * 2  # To prevent potential infinite loops
    
    while attempts < max_attempts:
        attempts += 1
        card_id = random.choice(pineappleonpizza_card_ids)
        cursor.execute('SELECT 1 FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card_id))
        if cursor.fetchone() is None:
            break

    if card_id is None:
        await ctx.author.send("No available cards to add to your inventory.")
        conn.close()
        return

    card = get_card_by_id(card_id)
    if card:
        card.copies += 1
        add_card(card)
        add_card_to_inventory(ctx.author.id, card.card_id)

        cursor.execute('UPDATE players SET pineappleonpizza = 1 WHERE user_id = ?', (ctx.author.id,))
        conn.commit()
        
        embed = discord.Embed(title="Special Drop", description="You have received a special card drop! Shh, don't tell anyone about this command.")
        embed.add_field(name="Name", value=card.name, inline=True)
        embed.add_field(name="ID", value=card.card_id, inline=True)
        embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
        embed.add_field(name="Type", value=card.card_type, inline=True)
        embed.add_field(name="Attack", value=card.attack, inline=True)
        embed.add_field(name="Defense", value=card.defense, inline=True)
        embed.add_field(name="Speed", value=card.speed, inline=True)
        embed.add_field(name="Overall", value=card.overall, inline=True)
        embed.add_field(name="League", value=card.league, inline=True)
        embed.add_field(name="Nation", value=card.nation, inline=True)
        embed.add_field(name="Copies", value=card.copies, inline=True)
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.author.send(embed=embed, file=discord.File(card.image_path))
        logger.info(f'{ctx.author.name} received a special card {card.name} (ID: {card.card_id}) using !pineappleonpizza')
    else:
        await ctx.author.send("An error occurred while processing your request.")
    
    conn.close()



#--------------------GERMANY

mannschaft_card_ids = [10417, 10447, 10449, 10452, 10463]

@bot.command(name='mannschaft')
@secret_command()
async def mannschaft(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT mannschaft FROM players WHERE user_id = ?', (ctx.author.id,))
    used_command = cursor.fetchone()[0]

    if used_command:
        await ctx.author.send("You have already used this command.")
        return
    
    card_id = None
    attempts = 0
    max_attempts = len(mannschaft_card_ids) * 2  # To prevent potential infinite loops
    
    while attempts < max_attempts:
        attempts += 1
        card_id = random.choice(mannschaft_card_ids)
        cursor.execute('SELECT 1 FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card_id))
        if cursor.fetchone() is None:
            break

    if card_id is None:
        await ctx.author.send("No available cards to add to your inventory.")
        conn.close()
        return

    card = get_card_by_id(card_id)
    if card:
        card.copies += 1
        add_card(card)
        add_card_to_inventory(ctx.author.id, card.card_id)

        cursor.execute('UPDATE players SET mannschaft = 1 WHERE user_id = ?', (ctx.author.id,))
        conn.commit()
        
        embed = discord.Embed(title="Special Drop", description="You have received a special card drop! Shh, don't tell anyone about this command.")
        embed.add_field(name="Name", value=card.name, inline=True)
        embed.add_field(name="ID", value=card.card_id, inline=True)
        embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
        embed.add_field(name="Type", value=card.card_type, inline=True)
        embed.add_field(name="Attack", value=card.attack, inline=True)
        embed.add_field(name="Defense", value=card.defense, inline=True)
        embed.add_field(name="Speed", value=card.speed, inline=True)
        embed.add_field(name="Overall", value=card.overall, inline=True)
        embed.add_field(name="League", value=card.league, inline=True)
        embed.add_field(name="Nation", value=card.nation, inline=True)
        embed.add_field(name="Copies", value=card.copies, inline=True)
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.author.send(embed=embed, file=discord.File(card.image_path))
        logger.info(f'{ctx.author.name} received a special card {card.name} (ID: {card.card_id}) using !mannschaft')
    else:
        await ctx.author.send("An error occurred while processing your request.")
    
    conn.close()


#--------------------NETHERLANDS

theflyingdutchmen_card_ids = [10420, 10422, 10424, 10432, 10433, 10448, 10456]

@bot.command(name='theflyingdutchmen')
@secret_command()
async def theflyingdutchmen(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT theflyingdutchmen FROM players WHERE user_id = ?', (ctx.author.id,))
    used_command = cursor.fetchone()[0]

    if used_command:
        await ctx.author.send("You have already used this command.")
        return
    
    card_id = None
    attempts = 0
    max_attempts = len(theflyingdutchmen_card_ids) * 2  # To prevent potential infinite loops
    
    while attempts < max_attempts:
        attempts += 1
        card_id = random.choice(theflyingdutchmen_card_ids)
        cursor.execute('SELECT 1 FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card_id))
        if cursor.fetchone() is None:
            break

    if card_id is None:
        await ctx.author.send("No available cards to add to your inventory.")
        conn.close()
        return

    card = get_card_by_id(card_id)
    if card:
        card.copies += 1
        add_card(card)
        add_card_to_inventory(ctx.author.id, card.card_id)

        cursor.execute('UPDATE players SET theflyingdutchmen = 1 WHERE user_id = ?', (ctx.author.id,))
        conn.commit()
        
        embed = discord.Embed(title="Special Drop", description="You have received a special card drop! Shh, don't tell anyone about this command.")
        embed.add_field(name="Name", value=card.name, inline=True)
        embed.add_field(name="ID", value=card.card_id, inline=True)
        embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
        embed.add_field(name="Type", value=card.card_type, inline=True)
        embed.add_field(name="Attack", value=card.attack, inline=True)
        embed.add_field(name="Defense", value=card.defense, inline=True)
        embed.add_field(name="Speed", value=card.speed, inline=True)
        embed.add_field(name="Overall", value=card.overall, inline=True)
        embed.add_field(name="League", value=card.league, inline=True)
        embed.add_field(name="Nation", value=card.nation, inline=True)
        embed.add_field(name="Copies", value=card.copies, inline=True)
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.author.send(embed=embed, file=discord.File(card.image_path))
        logger.info(f'{ctx.author.name} received a special card {card.name} (ID: {card.card_id}) using !theflyingdutchmen')
    else:
        await ctx.author.send("An error occurred while processing your request.")
    
    conn.close()

#--------------------FRANCE


blues_card_ids = [10398, 10410, 10419, 10421, 10426, 10439, 10467]

@bot.command(name='mayonnaise')
@secret_command()
async def blues(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT blues FROM players WHERE user_id = ?', (ctx.author.id,))
    used_command = cursor.fetchone()[0]

    if used_command:
        await ctx.author.send("You have already used this command.")
        return
    
    card_id = None
    attempts = 0
    max_attempts = len(blues_card_ids) * 2  # To prevent potential infinite loops
    
    while attempts < max_attempts:
        attempts += 1
        card_id = random.choice(blues_card_ids)
        cursor.execute('SELECT 1 FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card_id))
        if cursor.fetchone() is None:
            break

    if card_id is None:
        await ctx.author.send("No available cards to add to your inventory.")
        conn.close()
        return

    card = get_card_by_id(card_id)
    if card:
        card.copies += 1
        add_card(card)
        add_card_to_inventory(ctx.author.id, card.card_id)

        cursor.execute('UPDATE players SET blues = 1 WHERE user_id = ?', (ctx.author.id,))
        conn.commit()
        
        embed = discord.Embed(title="Special Drop", description="You have received a special card drop! Shh, don't tell anyone about this command.")
        embed.add_field(name="Name", value=card.name, inline=True)
        embed.add_field(name="ID", value=card.card_id, inline=True)
        embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
        embed.add_field(name="Type", value=card.card_type, inline=True)
        embed.add_field(name="Attack", value=card.attack, inline=True)
        embed.add_field(name="Defense", value=card.defense, inline=True)
        embed.add_field(name="Speed", value=card.speed, inline=True)
        embed.add_field(name="Overall", value=card.overall, inline=True)
        embed.add_field(name="League", value=card.league, inline=True)
        embed.add_field(name="Nation", value=card.nation, inline=True)
        embed.add_field(name="Copies", value=card.copies, inline=True)
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.author.send(embed=embed, file=discord.File(card.image_path))
        logger.info(f'{ctx.author.name} received a special card {card.name} (ID: {card.card_id}) using !blues')
    else:
        await ctx.author.send("An error occurred while processing your request.")
    
    conn.close()

#---------------------------------------------------------FACTS-------------------------------------------------------------------------------------


facts_list = [
    "England's last FIFA World Cup victory was in 1966, when they triumphed at Wembley Stadium, a moment the fans nostalgically reminisce about, since when they began their famous chant.",
    "Football is one of the best things to come out of France after their food, with their iconic 1998 World Cup victory on home soil showcasing the team's flair and elegance.",
    "Brazil holds the record for the most FIFA World Cup wins, with a total of five championships, known for their beautiful style of play that dazzles spectators.",
    "The Netherlands, known for their 'Total Football' style, reached the FIFA World Cup final three times but have yet to win the tournament, earning the nickname for their graceful and flying playstyle.",
    "Italy is renowned for its strong defensive tactics and has won the FIFA World Cup four times, with their latest victory in 2006, a victory almost as controversial as certain tropical toppings on pizza.",
    "Germany has a storied football history, having won the FIFA World Cup four times, and is known for their consistent performance in international tournaments, embodying the spirit of their beloved 'Fußball'."
]

@bot.command(name='facts')
async def facts(ctx):
    fact = random.choice(facts_list)
    embed = discord.Embed(title="Football Fact", description=fact, color=discord.Color.blue())
    await ctx.send(embed=embed)
    logger.info(f'{ctx.author.name} used the facts command and received: {fact}')
#---------------------------------------------------------CARDS AND PLAYERS CLASS-------------------------------------------------------------------------------------


class Card:
    def __init__(self, card_id, player_id, name, attack, defense, speed, height, club, position, overall, image_path, card_rarity=None, card_type='standard', league=None, nation=None, copies=0):
        self.card_id = card_id
        self.player_id = player_id
        self.name = name
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.height = height
        self.club = club
        self.position = position
        self.overall = overall if overall is not None else 0
        self.image_path = image_path
        self.card_rarity = card_rarity if card_rarity else determine_card_rarity(overall)
        self.card_type = card_type
        self.league = league
        self.nation = nation
        self.copies = copies


class Player:
    def __init__(self, user_id, name, battles_played=0, battles_won=0, battles_lost=0, has_claimed_starter_pack=False):
        self.user_id = user_id
        self.name = name
        self.battles_played = battles_played
        self.battles_won = battles_won
        self.battles_lost = battles_lost
        self.has_claimed_starter_pack = has_claimed_starter_pack
        self.selected_deck = None
        self.decks = {}

def ensure_player_exists(user_id, user_name):
    cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO players (user_id, name) VALUES (?, ?)', (user_id, user_name))
        conn.commit()

def add_card(card):
    card_rarity = determine_card_rarity(card.overall)
    cursor.execute('''
    INSERT INTO cards (card_id, player_id, name, attack, defense, speed, height, club, position, overall, image_path, card_rarity, card_type, league, nation, copies)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(card_id) DO UPDATE SET copies = copies + 1
    ''', (card.card_id, card.player_id, card.name, card.attack, card.defense, card.speed, card.height, card.club, card.position, card.overall, card.image_path, card_rarity, card.card_type, card.league, card.nation, card.copies))
    conn.commit()


def get_card_by_name(card_name):
    cursor.execute('SELECT * FROM cards')
    rows = cursor.fetchall()
    cards = [Card(*row) for row in rows]
    card_names = [card.name.lower() for card in cards]
    best_match = process.extractOne(card_name.lower(), card_names)
    if best_match:
        best_match_index = card_names.index(best_match[0])
        return cards[best_match_index]
    return None


def add_card_to_inventory(user_id, card_id):
    # Check if the card is already in the user's inventory
    cursor.execute('SELECT * FROM inventories WHERE user_id = ? AND card_id = ?', (user_id, card_id))
    if cursor.fetchone() is not None:
        raise ValueError("Card already in inventory")

    # Get the current copies number from the cards table
    cursor.execute('SELECT copies FROM cards WHERE card_id = ?', (card_id,))
    current_copies = cursor.fetchone()[0]

    # Set the edition to the current copies number + 1
    edition = current_copies 

    cursor.execute('''
    INSERT INTO inventories (user_id, card_id, edition) VALUES (?, ?, ?)
    ''', (user_id, card_id, edition))
    conn.commit()




def get_player_inventory(user_id):
    cursor.execute('''
    SELECT cards.*, inventories.edition FROM cards
    JOIN inventories ON cards.card_id = inventories.card_id
    WHERE inventories.user_id = ?
    ORDER BY cards.overall DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    return [Card(*row[:-1]) for row in rows], [row[-1] for row in rows]

def fetch_all_cards():
    cursor.execute('SELECT * FROM cards')
    rows = cursor.fetchall()
    return [Card(*row) for row in rows]


all_cards = fetch_all_cards()

# Define weights for each overall rating range
weight_70_79 = 70
weight_80_85 = 20
weight_86_90 = 7
weight_90_plus = 3
weight_non_standard_80 = 2
weight_non_standard_90 = 1

cards_with_weights = [(card, weight_70_79) for card in all_cards if 70 <= card.overall <= 79 and card.card_type == 'Standard'] + \
                     [(card, weight_80_85) for card in all_cards if 80 <= card.overall <= 85 and card.card_type == 'Standard'] + \
                     [(card, weight_86_90) for card in all_cards if 86 <= card.overall <= 90 and card.card_type == 'Standard'] + \
                     [(card, weight_90_plus) for card in all_cards if card.overall > 90 and card.card_type == 'Standard'] + \
                     [(card, weight_non_standard_80) for card in all_cards if 80 <= card.overall <= 89 and card.card_type != 'Standard'] + \
                     [(card, weight_non_standard_90) for card in all_cards if card.overall > 90 and card.card_type != 'Standard']

def get_card_weight_by_name(card_name):
    card = get_card_by_name(card_name)
    if not card:
        return None, None

    cursor = conn.cursor()

    if card.card_type == 'Standard':
        cursor.execute('SELECT COUNT(*) FROM cards WHERE card_type = "Standard"')
        total_standard_cards = cursor.fetchone()[0]

        if 70 <= card.overall <= 79:
            return weight_70_79 / total_standard_cards, card.name
        elif 80 <= card.overall <= 85:
            return weight_80_85 / total_standard_cards, card.name
        elif 86 <= card.overall <= 90:
            return weight_86_90 / total_standard_cards, card.name
        elif card.overall > 90:
            return weight_90_plus / total_standard_cards, card.name
        
    else:
        cursor.execute('SELECT COUNT(*) FROM cards WHERE card_type != "Standard"')
        total_non_standard_cards = cursor.fetchone()[0]
        return 3 / total_non_standard_cards, card.name



@bot.command(name='weight')
async def weight(ctx, *, card_name: str):
    weight, actual_card_name = get_card_weight_by_name(card_name)
    if weight:
        embed = discord.Embed(title=f"Card Weight: {actual_card_name}", color=0x00ff00)
        embed.add_field(name="Pack Weight", value=f"{weight:.6f}", inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Card Not Found", color=0xff0000)
        embed.add_field(name="Error", value=f"Card '{card_name}' not found or does not have a defined weight.", inline=False)
        await ctx.send(embed=embed)


class CollectButton(discord.ui.Button):
    def __init__(self, card, channel):
        super().__init__(style=discord.ButtonStyle.green, label="Collect", custom_id="collect_card")
        self.card = card
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        ensure_player_exists(interaction.user.id, interaction.user.name)
        add_card_to_inventory(interaction.user.id, self.card.card_id)
        await interaction.response.send_message(f'{interaction.user.name} collected {self.card.name}!', ephemeral=True)
        await self.channel.send(f'{interaction.user.mention} collected {self.card.name}!')
        self.view.stop()

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    card_drop.start()

def weighted_choice(cards_with_weights):
    total = sum(weight for card, weight in cards_with_weights)
    r = random.uniform(0, total)
    upto = 0
    for card, weight in cards_with_weights:
        if upto + weight >= r:
            return card
        upto += weight

@tasks.loop(minutes=30)
async def card_drop():
    channel = bot.get_channel(1255230565875978240)  # Replace with your channel ID
    card = weighted_choice(cards_with_weights)
    
    add_card(card)

    embed = discord.Embed(title="Card Drop!", description="A new card is available!")
    embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
    view = discord.ui.View(timeout=60)  # 1 minute timeout
    view.add_item(CollectButton(card, channel))
    
    msg = await channel.send(embed=embed, view=view, file=discord.File(card.image_path))
    
    await asyncio.sleep(60)  # 1 minute timeout
    if not view.is_finished():
        await msg.edit(content="The card drop has expired!", view=None)



@bot.command(name='get_starter_pack')
async def get_starter_pack(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    cursor.execute('SELECT has_claimed_starter_pack FROM players WHERE user_id = ?', (ctx.author.id,))
    has_claimed_starter_pack = cursor.fetchone()[0]
    if has_claimed_starter_pack:
        await ctx.send("You have already claimed your starter pack!")
        return

    common_pack = random.sample([card for card in all_cards if 70 <= card.overall <= 79], 6)
    uncommon_pack = random.sample([card for card in all_cards if 80 <= card.overall <= 85], 3)
    rare_pack = random.sample([card for card in all_cards if card.overall > 85], 1)

    all_cards_received = common_pack + uncommon_pack + rare_pack

    for card in all_cards_received:
        add_card_to_inventory(ctx.author.id, card.card_id)
        increment_card_copies(card.card_id)

    cursor.execute('UPDATE players SET has_claimed_starter_pack = 1 WHERE user_id = ?', (ctx.author.id,))
    conn.commit()

    card_names = "\n".join([f"{card.name} (ID: {card.card_id})" for card in all_cards_received])
    await ctx.send(f"**{ctx.author.name} has claimed their starter pack!**\nYou received:\n{card_names}")
    logger.info(f'{ctx.author.name} claimed a starter pack')

def increment_card_copies(card_id):
    cursor.execute('UPDATE cards SET copies = copies + 1 WHERE card_id = ?', (card_id,))
    conn.commit()

#---------------------------------------------------------VIEW-------------------------------------------------------------------------------------

def get_card_by_name_or_id(identifier):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cards')
    rows = cursor.fetchall()
    conn.close()
    cards = [Card(*row) for row in rows]
    
    if identifier.isdigit():
        for card in cards:
            if card.card_id == int(identifier):
                return [card]
    else:
        card_names = [card.name.lower() for card in cards]
        best_matches = process.extract(identifier.lower(), card_names, limit=5)
        matched_cards = [cards[card_names.index(match[0])] for match in best_matches if match[1] > 80]  # Adjust threshold as needed
        if matched_cards:
            return matched_cards
    
    return None


from discord.ui import Select, View

class ViewCardSelect(discord.ui.Select):
    def __init__(self, cards, user):
        options = [discord.SelectOption(label=card.name, description=f"ID: {card.card_id}", value=str(card.card_id)) for card in cards]
        super().__init__(placeholder="Select the card...", min_values=1, max_values=1, options=options)
        self.cards = cards
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        selected_card_id = int(self.values[0])
        selected_card = next(card for card in self.cards if card.card_id == selected_card_id)
        
        embed = discord.Embed(title=f"**{selected_card.name}**", color=discord.Color.blue())
        embed.add_field(name="ID", value=selected_card.card_id, inline=True)
        embed.add_field(name="Rarity", value=selected_card.card_rarity, inline=True)
        embed.add_field(name="Type", value=selected_card.card_type, inline=True)
        embed.add_field(name="Attack", value=selected_card.attack, inline=True)
        embed.add_field(name="Defense", value=selected_card.defense, inline=True)
        embed.add_field(name="Speed", value=selected_card.speed, inline=True)
        embed.add_field(name="Height", value=selected_card.height, inline=True)
        embed.add_field(name="Club", value=selected_card.club, inline=True)
        embed.add_field(name="Position", value=selected_card.position, inline=True)
        embed.add_field(name="Overall", value=selected_card.overall, inline=True)
        embed.add_field(name="League", value=selected_card.league, inline=True)
        embed.add_field(name="Nation", value=selected_card.nation, inline=True)
        embed.add_field(name="Copies", value=selected_card.copies, inline=True)
        embed.set_image(url=f"attachment://{selected_card.image_path.split('/')[-1]}")
        embed.set_footer(text=f"Requested by {self.user.name}", icon_url=self.user.avatar.url)

        await interaction.response.send_message(embed=embed, file=discord.File(selected_card.image_path))
        logger.info(f'{self.user.name} viewed card {selected_card.name} (ID: {selected_card.card_id})')

class ViewCardSelectView(View):
    def __init__(self, cards, user):
        super().__init__(timeout=60)
        self.add_item(ViewCardSelect(cards, user))



@bot.command(name='view')
async def view(ctx, *, identifier: str):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    cards = get_card_by_name_or_id(identifier)
    if cards:
        if len(cards) == 1:
            card = cards[0]
            
            # Check if the user owns the card
            cursor.execute('SELECT trade_count FROM inventories WHERE user_id = ? AND card_id = ?', (ctx.author.id, card.card_id))
            inventory_entry = cursor.fetchone()
            owned_by_user = "Yes" if inventory_entry else "No"

            embed = discord.Embed(title=f"**{card.name}**", color=discord.Color.blue())
            embed.add_field(name="ID", value=card.card_id, inline=True)
            embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
            embed.add_field(name="Type", value=card.card_type, inline=True)
            embed.add_field(name="Attack", value=card.attack, inline=True)
            embed.add_field(name="Defense", value=card.defense, inline=True)
            embed.add_field(name="Speed", value=card.speed, inline=True)
            embed.add_field(name="Height", value=card.height, inline=True)
            embed.add_field(name="Club", value=card.club, inline=True)
            embed.add_field(name="Position", value=card.position, inline=True)
            embed.add_field(name="Overall", value=card.overall, inline=True)
            embed.add_field(name="League", value=card.league, inline=True)
            embed.add_field(name="Nation", value=card.nation, inline=True)
            embed.add_field(name="Copies", value=card.copies, inline=True)
            embed.add_field(name="Owned by User", value=owned_by_user, inline=True)
            
            # Add Ownership field if the card is owned by the user
            if owned_by_user == "Yes":
                trade_count = inventory_entry[0]
                ownership = "First Owner" if trade_count == 0 else "Traded In"
                embed.add_field(name="Ownership", value=ownership, inline=True)

            embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

            await ctx.send(embed=embed, file=discord.File(card.image_path))
            logger.info(f'{ctx.author.name} viewed card {card.name} (ID: {card.card_id})')
        else:
            view = ViewCardSelectView(cards, ctx.author)
            await ctx.send("Multiple cards found, please select one:", view=view)
    else:
        await ctx.send(f'No card found with the identifier {identifier}')
        logger.info(f'{ctx.author.name} tried to view card with identifier {identifier} but it was not found')



#---------------------------------------------------------DROPS-------------------------------------------------------------------------------------


@bot.command(name='daily')
@commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hours cooldown per user
async def daily(ctx):
    logger.info(f"User {ctx.author.name} (ID: {ctx.author.id}) invoked the daily command.")
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    # Generate two cards
    cards = [weighted_choice(cards_with_weights) for _ in range(2)]
    for card in cards:
        card.copies += 1

    if increment_cards_dropped(ctx.author.id):  # Increment cards_dropped
        logger.info(f"User {ctx.author.name}'s cards_dropped incremented successfully.")
    else:
        logger.error(f"Failed to increment cards_dropped for user {ctx.author.name}.")

    logger.info(f"Generated cards for {ctx.author.name}: {[card.name for card in cards]}")

    content = f'{ctx.author.mention}, you have a daily reward card to collect. Please choose one of the following cards:'

    view = discord.ui.View(timeout=60)
    for card in cards:
        view.add_item(CollectCardButton(card, ctx.author.id))

    embed = discord.Embed(title="Daily Reward", description="Please choose one of the following cards:", color=0x00ff00)
    
    for i, card in enumerate(cards, 1):
        embed.add_field(name=f"Card {i} - {card.name}", value=(
            f"**ID:** {card.card_id}\n"
            f"**Rarity:** {card.card_rarity}\n"
            f"**Type:** {card.card_type}\n"
            f"**Attack:** {card.attack}\n"
            f"**Defense:** {card.defense}\n"
            f"**Speed:** {card.speed}\n"
            f"**Overall:** {card.overall}\n"
            f"**League:** {card.league}\n"
            f"**Nation:** {card.nation}\n"
            f"**Copies:** {card.copies}\n"
        ), inline=True)
    
    # Add the images of the cards
    for i, card in enumerate(cards):
        embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")

    files = [discord.File(card.image_path) for card in cards]

    try:
        await ctx.send(content=content, embed=embed, view=view, files=files)
        logger.info(f"Sent daily reward message to {ctx.author.name}")
    except Exception as e:
        logger.error(f"Failed to send daily reward message to {ctx.author.name}: {e}")

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = int(error.retry_after)
        hours, remainder = divmod(retry_after, 3600)
        minutes, _ = divmod(remainder, 60)
        await ctx.send(f"You have already claimed your daily reward. Please wait {hours} hours and {minutes} minutes to claim it again.")
        logger.info(f"User {ctx.author.name} tried to claim daily reward but is on cooldown: {hours} hours and {minutes} minutes remaining.")



@bot.command(name='drop')
@commands.cooldown(1, 1800, commands.BucketType.user)  # 30 minutes cooldown per user
async def drop_card(ctx):
    logger.info(f"User {ctx.author.name} (ID: {ctx.author.id}) invoked the drop command.")
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    # Generate a card
    card = weighted_choice(cards_with_weights)
    card.copies += 1
    add_card(card)
    
    if increment_cards_dropped(ctx.author.id):  # Increment cards_dropped
        logger.info(f"User {ctx.author.name}'s cards_dropped incremented successfully.")
    else:
        logger.error(f"Failed to increment cards_dropped for user {ctx.author.name}.")

    logger.info(f"Generated card for {ctx.author.name}: {card.name} (ID: {card.card_id})")

    content = f'{ctx.author.mention}, you have a card drop to collect:'
    embed = discord.Embed(title="Card Drop")
    embed.add_field(name="Name", value=card.name, inline=True)
    embed.add_field(name="ID", value=card.card_id, inline=True)
    embed.add_field(name="Rarity", value=card.card_rarity, inline=True)
    embed.add_field(name="Type", value=card.card_type, inline=True)
    embed.add_field(name="Attack", value=card.attack, inline=True)
    embed.add_field(name="Defense", value=card.defense, inline=True)
    embed.add_field(name="Speed", value=card.speed, inline=True)
    embed.add_field(name="Overall", value=card.overall, inline=True)
    embed.add_field(name="League", value=card.league, inline=True)
    embed.add_field(name="Nation", value=card.nation, inline=True)
    embed.add_field(name="Copies", value=card.copies, inline=True)
    embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")

    view = View(timeout=60)
    view.add_item(CollectCardButton(card, ctx.author.id))

    try:
        await ctx.send(content=content, embed=embed, view=view, file=discord.File(card.image_path))
        logger.info(f"Sent card drop message to {ctx.author.name}")
    except Exception as e:
        logger.error(f"Failed to send card drop message to {ctx.author.name}: {e}")

@drop_card.error
async def drop_card_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry_after = int(error.retry_after)
        minutes, seconds = divmod(retry_after, 60)
        await ctx.send(f"This command is on cooldown. Please wait {minutes} minutes and {seconds} seconds to use it again.")
        logger.info(f"User {ctx.author.name} tried to drop a card but is on cooldown: {minutes} minutes and {seconds} seconds remaining.")





def increment_cards_dropped(user_id):
    try:
        connection = sqlite3.connect('cards_game.db')
        cursor = connection.cursor()
        cursor.execute('UPDATE players SET cards_dropped = cards_dropped + 1 WHERE user_id = ?', (user_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except sqlite3.Error as e:
        logger.error(f'SQLite error: {e}')
        return False

#---------------------------------------------------------STATS-------------------------------------------------------------------------------------

@bot.command(name='stats')
async def stats(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    ensure_player_exists(member.id, member.name)
    cursor.execute('SELECT * FROM players WHERE user_id = ?', (member.id,))
    player = cursor.fetchone()
    if player:
        embed = discord.Embed(title=f"**{player[1]}'s Stats**")

        # Add display title
        display_title = player[16] if player[16] else "No Title Set"
        embed.add_field(name="**Title**", value=display_title, inline=False)

        embed.add_field(name="**Battles Played**", value=player[2])
        embed.add_field(name="**Battles Won**", value=player[3])
        embed.add_field(name="**Battles Lost**", value=player[4])
        embed.add_field(name="**Rounds Played**", value=player[6])
        embed.add_field(name="**Rounds Won**", value=player[7])
        embed.add_field(name="**Rounds Lost**", value=player[8])

        cards, editions = get_player_inventory(player[0])
        total_cards = len(cards)
        common_cards = sum(1 for card in cards if card.card_rarity == 'Common')
        uncommon_cards = sum(1 for card in cards if card.card_rarity == 'Uncommon')
        rare_cards = sum(1 for card in cards if card.card_rarity == 'Rare')

        embed.add_field(name="**Total Cards**", value=total_cards)
        embed.add_field(name="**Common Cards**", value=common_cards)
        embed.add_field(name="**Uncommon Cards**", value=uncommon_cards)
        embed.add_field(name="**Rare Cards**", value=rare_cards)

        await ctx.send(embed=embed)
        logger.info(f'{ctx.author.name} viewed {member.name}\'s stats')
    else:
        await ctx.send("Player not found.")
        logger.info(f'{ctx.author.name} tried to view stats but no player found')


class TitleDropdown(discord.ui.Select):
    def __init__(self, titles, user_id):
        options = [discord.SelectOption(label=title, value=str(achievement_id)) for title, achievement_id in titles]
        super().__init__(placeholder="Choose a title...", options=options)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        achievement_id = int(self.values[0])
        cursor.execute('SELECT title FROM achievements WHERE achievement_id = ?', (achievement_id,))
        title = cursor.fetchone()[0]
        
        cursor.execute('UPDATE players SET display_title = ? WHERE user_id = ?', (title, self.user_id))
        conn.commit()

        await interaction.response.send_message(f"Your title has been set to: {title}", ephemeral=True)
        logger.info(f'{interaction.user.name} set their title to {title}')

class TitleDropdownView(discord.ui.View):
    def __init__(self, titles, user_id):
        super().__init__(timeout=60)
        self.add_item(TitleDropdown(titles, user_id))


@bot.command(name='set_title')
async def set_title(ctx):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    
    cursor.execute('''
    SELECT achievements.title, achievements.achievement_id
    FROM achievements
    JOIN user_achievements ON achievements.achievement_id = user_achievements.achievement_id
    WHERE user_achievements.user_id = ?
    ''', (ctx.author.id,))
    titles = cursor.fetchall()

    if titles:
        view = TitleDropdownView(titles, ctx.author.id)
        await ctx.send("Choose a title from the dropdown menu below:", view=view)
        logger.info(f'{ctx.author.name} is setting a title')
    else:
        await ctx.send("You have no titles to set.")
        logger.info(f'{ctx.author.name} tried to set a title but has no achievements')



import discord
from discord.ui import Button

class CollectCardButton(Button):
    def __init__(self, card, user_id):
        super().__init__(label=f"Collect {card.name}", style=discord.ButtonStyle.green)
        self.card = card
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot collect this card.", ephemeral=True)
            return

        try:
            add_card_to_inventory(self.user_id, self.card.card_id)
            await interaction.response.send_message(f'{interaction.user.name} collected {self.card.name}!', ephemeral=True)

            # Update the embed to reflect the collected card
            embed = interaction.message.embeds[0]
            embed.title = "Card Collected!"
            embed.description = f"{interaction.user.mention} has collected {self.card.name}!"
            embed.color = discord.Color.green()
            embed.set_image(url=f"attachment://{self.card.image_path.split('/')[-1]}")

            await interaction.message.edit(content=None, embed=embed, view=None)
            logger.info(f"{interaction.user.name} collected card {self.card.name} (ID: {self.card.card_id})")
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)


def get_user_rank_and_details(user_id, criteria):
    cursor.execute(f'SELECT user_id, name, {criteria}, ROW_NUMBER() OVER (ORDER BY {criteria} DESC) as rank FROM players')
    rows = cursor.fetchall()
    for row in rows:
        if row[0] == user_id:
            return row
    return None

# Default leaderboard for battles won
@bot.group(name='lb', invoke_without_command=True)
async def leaderboard(ctx):
    cursor.execute('SELECT * FROM players ORDER BY battles_won DESC LIMIT 10')
    rows = cursor.fetchall()
    embed = discord.Embed(title="**Leaderboard - Battles Won**")
    for i, row in enumerate(rows, start=1):
        embed.add_field(name=f"**{i}. {row[1]}**", value=f"**Battles Won:** {row[3]}", inline=False)

    user_rank = get_user_rank_and_details(ctx.author.id, 'battles_won')
    if user_rank and user_rank[3] > 10:
        embed.add_field(name=f"Your Rank: {user_rank[3]}", value=f"**{user_rank[1]}** - Battles Won: {user_rank[2]}", inline=False)

    await ctx.send(embed=embed)
    logger.info(f'{ctx.author.name} viewed the leaderboard for battles won')

# Subcommands for other leaderboard criteria
@leaderboard.command(name='bp')
async def leaderboard_battles_played(ctx):
    cursor.execute('SELECT * FROM players ORDER BY battles_played DESC LIMIT 10')
    rows = cursor.fetchall()
    embed = discord.Embed(title="**Leaderboard - Battles Played**")
    for i, row in enumerate(rows, start=1):
        embed.add_field(name=f"**{i}. {row[1]}**", value=f"**Battles Played:** {row[2]}", inline=False)

    user_rank = get_user_rank_and_details(ctx.author.id, 'battles_played')
    if user_rank and user_rank[3] > 10:
        embed.add_field(name=f"Your Rank: {user_rank[3]}", value=f"**{user_rank[1]}** - Battles Played: {user_rank[2]}", inline=False)

    await ctx.send(embed=embed)
    logger.info(f'{ctx.author.name} viewed the leaderboard for battles played')

@leaderboard.command(name='rw')
async def leaderboard_rounds_won(ctx):
    cursor.execute('SELECT * FROM players ORDER BY rounds_won DESC LIMIT 10')
    rows = cursor.fetchall()
    embed = discord.Embed(title="**Leaderboard - Rounds Won**")
    for i, row in enumerate(rows, start=1):
        embed.add_field(name=f"**{i}. {row[1]}**", value=f"**Rounds Won:** {row[7]}", inline=False)

    user_rank = get_user_rank_and_details(ctx.author.id, 'rounds_won')
    if user_rank and user_rank[3] > 10:
        embed.add_field(name=f"Your Rank: {user_rank[3]}", value=f"**{user_rank[1]}** - Rounds Won: {user_rank[2]}", inline=False)

    await ctx.send(embed=embed)
    logger.info(f'{ctx.author.name} viewed the leaderboard for rounds won')

@leaderboard.command(name='rp')
async def leaderboard_rounds_played(ctx):
    cursor.execute('SELECT * FROM players ORDER BY rounds_played DESC LIMIT 10')
    rows = cursor.fetchall()
    embed = discord.Embed(title="**Leaderboard - Rounds Played**")
    for i, row in enumerate(rows, start=1):
        embed.add_field(name=f"**{i}. {row[1]}**", value=f"**Rounds Played:** {row[6]}", inline=False)

    user_rank = get_user_rank_and_details(ctx.author.id, 'rounds_played')
    if user_rank and user_rank[3] > 10:
        embed.add_field(name=f"Your Rank: {user_rank[3]}", value=f"**{user_rank[1]}** - Rounds Played: {user_rank[2]}", inline=False)

    await ctx.send(embed=embed)
    logger.info(f'{ctx.author.name} viewed the leaderboard for rounds played')


import logging
logger = logging.getLogger(__name__)

@bot.command(name='inventory')
async def view_inventory(ctx, user: discord.User = None):
    if user is None:
        user = ctx.author

    ensure_player_exists(user.id, user.name)
    inventory, editions = get_player_inventory(user.id)
    if inventory:
        view = InventoryView(inventory, user, editions)
        embed = view.update_view()
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        logger.info(f'{ctx.author.name} viewed {user.name}\'s inventory')
    else:
        await ctx.send(f"{user.name} has no cards in their inventory.")
        logger.info(f'{ctx.author.name} tried to view {user.name}\'s inventory but it was empty')

class InventoryView(discord.ui.View):
    def __init__(self, inventory, user, editions):
        super().__init__(timeout=None)
        self.inventory = inventory
        self.editions = editions
        self.user = user
        self.current_page = 0
        self.total_pages = (len(inventory) - 1) // 10 + 1
        self.message = None
        self.update_buttons()

    def update_view(self):
        start = self.current_page * 10
        end = start + 10
        cards = self.inventory[start:end]
        editions = self.editions[start:end]

        card_descriptions = [
            f"**{card.name} (ID: {card.card_id})** - Edition: {edition}, Overall: {card.overall}, Copies: {card.copies}, Attack: {card.attack}, Defense: {card.defense}, Speed: {card.speed}"
            for card, edition in zip(cards, editions)
        ]
        description = '\n'.join(card_descriptions) if card_descriptions else "No cards to display."

        embed = discord.Embed(title=f"{self.user.name}'s Inventory", description=description)
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages}")

        return embed

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.total_pages - 1:
            self.add_item(NextButton())

class PreviousButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Previous', style=discord.ButtonStyle.primary, custom_id='previous')

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page > 0:
            view.current_page -= 1
            embed = view.update_view()
            view.update_buttons()
            await interaction.response.edit_message(embed=embed, view=view)

class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Next', style=discord.ButtonStyle.primary, custom_id='next')

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page < view.total_pages - 1:
            view.current_page += 1
            embed = view.update_view()
            view.update_buttons()
            await interaction.response.edit_message(embed=embed, view=view)



#---------------------------------------------------------TRADES-------------------------------------------------------------------------------------


from discord.ui import View, Button

@bot.command(name='trade')
async def trade(ctx, your_card_id: int, other_user: discord.User, their_card_id: int):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    ensure_player_exists(other_user.id, other_user.name)

    # Fetch your card details
    cursor.execute('SELECT inventories.card_id, cards.name, cards.attack, cards.defense, cards.speed, cards.height, cards.club, cards.position, cards.overall, cards.image_path, cards.card_rarity, cards.card_type, cards.league, cards.nation FROM inventories JOIN cards ON inventories.card_id = cards.card_id WHERE inventories.user_id = ? AND inventories.card_id = ?', (ctx.author.id, your_card_id))
    your_card = cursor.fetchone()
    
    # Fetch their card details
    cursor.execute('SELECT inventories.card_id, cards.name, cards.attack, cards.defense, cards.speed, cards.height, cards.club, cards.position, cards.overall, cards.image_path, cards.card_rarity, cards.card_type, cards.league, cards.nation FROM inventories JOIN cards ON inventories.card_id = cards.card_id WHERE inventories.user_id = ? AND inventories.card_id = ?', (other_user.id, their_card_id))
    their_card = cursor.fetchone()

    # Log card details
    logger.info(f"Your card details: {your_card}")
    logger.info(f"Their card details: {their_card}")

    if not your_card or not their_card:
        await ctx.send("One of you does not own the card you're trying to trade.")
        return

    view = TradeView(ctx, your_card, other_user, their_card)
    embed = discord.Embed(title="Trade Offer", description=f"{ctx.author.name} wants to trade cards with {other_user.name}.")
    embed.add_field(name=f"{ctx.author.name}'s Card", value=f"**{your_card[1]}**\nAttack: {your_card[2]}, Defense: {your_card[3]}, Speed: {your_card[4]}, Height: {your_card[5]}, Club: {your_card[6]}, Position: {your_card[7]}, Overall: {your_card[8]}, Rarity: {your_card[10]}, Type: {your_card[11]}, League: {your_card[12]}, Nation: {your_card[13]}", inline=True)
    embed.add_field(name=f"{other_user.name}'s Card", value=f"**{their_card[1]}**\nAttack: {their_card[2]}, Defense: {their_card[3]}, Speed: {their_card[4]}, Height: {their_card[5]}, Club: {their_card[6]}, Position: {their_card[7]}, Overall: {their_card[8]}, Rarity: {their_card[10]}, Type: {their_card[11]}, League: {their_card[12]}, Nation: {their_card[13]}", inline=True)
    embed.set_image(url=f"attachment://{your_card[9].split('/')[-1]}")
    embed.set_thumbnail(url=f"attachment://{their_card[9].split('/')[-1]}")
    
    await ctx.send(embed=embed, view=view, files=[discord.File(your_card[9]), discord.File(their_card[9])])

class TradeView(discord.ui.View):
    def __init__(self, ctx, your_card, other_user, their_card):
        super().__init__(timeout=60)  # Timeout after 60 seconds
        self.ctx = ctx
        self.your_card = your_card
        self.other_user = other_user
        self.their_card = their_card

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.other_user.id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Log card details
        logger.info(f"Accept trade initiated by {interaction.user.id}")
        logger.info(f"Your card ID: {self.your_card[0]}")
        logger.info(f"Their card ID: {self.their_card[0]}")

        cursor.execute('SELECT card_id FROM inventories WHERE user_id = ? AND card_id = ?', (self.ctx.author.id, self.your_card[0]))
        your_card_check = cursor.fetchone()
        cursor.execute('SELECT card_id FROM inventories WHERE user_id = ? AND card_id = ?', (self.other_user.id, self.their_card[0]))
        their_card_check = cursor.fetchone()

        # Log card ownership check results
        logger.info(f"Your card after check: {your_card_check}")
        logger.info(f"Their card after check: {their_card_check}")

        if not your_card_check or not their_card_check:
            await self.ctx.send("One of you does not own the card you're trying to trade.")
            return

        # Check if users already have the cards they are being offered
        cursor.execute('SELECT card_id FROM inventories WHERE user_id = ? AND card_id = ?', (self.other_user.id, self.your_card[0]))
        other_user_has_your_card = cursor.fetchone()
        cursor.execute('SELECT card_id FROM inventories WHERE user_id = ? AND card_id = ?', (self.ctx.author.id, self.their_card[0]))
        you_have_their_card = cursor.fetchone()

        if other_user_has_your_card:
            await self.ctx.send(f"{self.other_user.name} already has the card **{self.your_card[1]}**.")
            return

        if you_have_their_card:
            await self.ctx.send(f"You already have the card **{self.their_card[1]}**.")
            return

        # Perform the trade
        cursor.execute('UPDATE inventories SET user_id = ? WHERE user_id = ? AND card_id = ?', (self.other_user.id, self.ctx.author.id, self.your_card[0]))
        cursor.execute('UPDATE inventories SET user_id = ? WHERE user_id = ? AND card_id = ?', (self.ctx.author.id, self.other_user.id, self.their_card[0]))
        conn.commit()

        await interaction.response.send_message(f"Trade completed! {self.ctx.author.name} traded card **{self.your_card[1]}** with {self.other_user.name}'s card **{self.their_card[1]}**.")
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Trade declined.")
        await self.ctx.send(f"{self.other_user.name} has declined the trade.")
        self.stop()


def add_deck(user_id, deck_name, card_ids):
    # Check if deck already exists
    cursor.execute('SELECT * FROM decks WHERE user_id = ? AND deck_name = ?', (user_id, deck_name))
    if cursor.fetchone() is not None:
        raise ValueError("Deck with this name already exists")

    # Check for duplicate player IDs in the deck
    player_ids = set()
    for card_id in card_ids:
        cursor.execute('SELECT player_id FROM cards WHERE card_id = ?', (card_id,))
        player_id = cursor.fetchone()[0]
        if player_id in player_ids:
            raise ValueError("Deck cannot contain more than one card with the same player ID")
        player_ids.add(player_id)

    # Convert card IDs to comma-separated string
    cards_str = ','.join(map(str, card_ids))

    # Insert the deck into the database
    cursor.execute('INSERT INTO decks (user_id, deck_name, cards) VALUES (?, ?, ?)', (user_id, deck_name, cards_str))
    conn.commit()


def get_deck(user_id, deck_name):
    cursor.execute('SELECT cards FROM decks WHERE user_id = ? AND deck_name = ?', (user_id, deck_name))
    result = cursor.fetchone()
    if result is None:
        return None
    return list(map(int, result[0].split(',')))


@bot.command(name='create_deck')
async def create_deck(ctx, deck_name: str, *card_ids: int):
    if len(card_ids) != 5:
        await ctx.send("A deck must contain exactly 5 cards.")
        return

    ensure_player_exists(ctx.author.id, ctx.author.name)

    try:
        add_deck(ctx.author.id, deck_name, card_ids)
        await ctx.send(f"Deck '{deck_name}' created successfully with cards: {', '.join(map(str, card_ids))}")
    except ValueError as e:
        await ctx.send(str(e))


@bot.command(name='view_deck')
async def view_deck(ctx, deck_name: str):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    deck = get_deck(ctx.author.id, deck_name)
    if deck is None:
        await ctx.send(f"No deck found with the name '{deck_name}'.")
        return

    card_details = []
    for card in deck:
        card_id = card.card_id if hasattr(card, 'card_id') else card  # Ensure card_id is an integer or string
        cursor.execute('SELECT name, attack, defense, speed, overall, image_path FROM cards WHERE card_id = ?', (card_id,))
        card_data = cursor.fetchone()
        if card_data:
            card_details.append(f"**{card_data[0]}**\nAttack: {card_data[1]}, Defense: {card_data[2]}, Speed: {card_data[3]}, Overall: {card_data[4]}")

    embed = discord.Embed(title=f"Deck '{deck_name}'", description="\n\n".join(card_details))
    await ctx.send(embed=embed)

from discord.ui import Select, View, Button


#---------------------------------------------------------BATTLES-------------------------------------------------------------------------------------

class Battle:
    def __init__(self, player1, player2, player1_deck, player2_deck, parent_view):
        self.player1 = player1
        self.player2 = player2
        self.player1_deck = player1_deck
        self.player2_deck = player2_deck
        self.turn = random.choice([player1, player2])
        self.player1_wins = 0
        self.player2_wins = 0
        self.round = 1
        self.max_rounds = 5
        self.player1_action = None
        self.player2_action = None
        self.parent_view = parent_view
        self.player1_used_cards = []
        self.player2_used_cards = []

    def get_deck(self, player):
        if player == self.player1:
            return [card for card in self.player1_deck if card not in self.player1_used_cards]
        else:
            return [card for card in self.player2_deck if card not in self.player2_used_cards]

    async def resolve_battle(self, interaction):
        player1_card = self.player1_card
        player2_card = self.player2_card

        self.player1_used_cards.append(player1_card)
        self.player2_used_cards.append(player2_card)

        round_result = ""

        if self.player1_action == 'attack' and self.player2_action == 'defense':
            if player1_card.attack > player2_card.defense:
                self.player1_wins += 1
                round_result = f"{self.player1.name} wins the round with Attack vs Defense!"
                await self.update_round_stats(self.player1, self.player2, interaction)
            elif player1_card.attack < player2_card.defense:
                self.player2_wins += 1
                round_result = f"{self.player2.name} wins the round with Defense vs Attack!"
                await self.update_round_stats(self.player2, self.player1, interaction)
            else:
                round_result = "It's a draw!"
        elif self.player1_action == 'defense' and self.player2_action == 'attack':
            if player1_card.defense > player2_card.attack:
                self.player1_wins += 1
                round_result = f"{self.player1.name} wins the round with Defense vs Attack!"
                await self.update_round_stats(self.player1, self.player2, interaction)
            elif player1_card.defense < player2_card.attack:
                self.player2_wins += 1
                round_result = f"{self.player2.name} wins the round with Attack vs Defense!"
                await self.update_round_stats(self.player2, self.player1, interaction)
            else:
                round_result = "It's a draw!"
        elif self.player1_action == 'speed' and self.player2_action == 'speed':
            if player1_card.speed > player2_card.speed:
                self.player1_wins += 1
                round_result = f"{self.player1.name} wins the round with Speed vs Speed!"
                await self.update_round_stats(self.player1, self.player2, interaction)
            elif player1_card.speed < player2_card.speed:
                self.player2_wins += 1
                round_result = f"{self.player2.name} wins the round with Speed vs Speed!"
                await self.update_round_stats(self.player2, self.player1, interaction)
            else:
                round_result = "It's a draw!"

        embed = discord.Embed(title="Round Result", description=round_result)
        embed.add_field(name=f"{self.player1.name}'s Card", value=f"Name: {player1_card.name}\nAttack: {player1_card.attack}\nDefense: {player1_card.defense}\nSpeed: {player1_card.speed}", inline=True)
        embed.add_field(name=f"{self.player2.name}'s Card", value=f"Name: {player2_card.name}\nAttack: {player2_card.attack}\nDefense: {player2_card.defense}\nSpeed: {player2_card.speed}", inline=True)
        await interaction.channel.send(embed=embed)

        del self.player1_card
        del self.player2_card
        self.player1_action = None
        self.player2_action = None

        self.turn = self.player2 if self.turn == self.player1 else self.player1
        self.round += 1

        if self.player1_wins >= 3:
            await self.update_battle_stats(self.player1, self.player2, interaction)
            embed = discord.Embed(title="Battle Result", description=f"{self.player1.name} wins the battle!")
            await interaction.channel.send(embed=embed)
            return
        elif self.player2_wins >= 3:
            await self.update_battle_stats(self.player2, self.player1, interaction)
            embed = discord.Embed(title="Battle Result", description=f"{self.player2.name} wins the battle!")
            await interaction.channel.send(embed=embed)
            return
        else:
            await self.parent_view.next_round(interaction)

    async def update_round_stats(self, winner, loser, interaction):
        cursor.execute('UPDATE players SET rounds_played = rounds_played + 1, rounds_won = rounds_won + 1 WHERE user_id = ?', (winner.id,))
        cursor.execute('UPDATE players SET rounds_played = rounds_played + 1, rounds_lost = rounds_lost + 1 WHERE user_id = ?', (loser.id,))
        conn.commit()
        await self.check_achievements(winner.id, 'rounds_won', interaction)

    async def update_battle_stats(self, winner, loser, interaction):
        cursor.execute('UPDATE players SET battles_played = battles_played + 1, battles_won = battles_won + 1 WHERE user_id = ?', (winner.id,))
        cursor.execute('UPDATE players SET battles_played = battles_played + 1, battles_lost = battles_lost + 1 WHERE user_id = ?', (loser.id,))
        conn.commit()
        await self.check_achievements(winner.id, 'battles_won', interaction)

    async def check_achievements(self, user_id, stat_type, interaction):
        conn = sqlite3.connect('cards_game.db')
        cursor = conn.cursor()

        cursor.execute(f'SELECT {stat_type} FROM players WHERE user_id = ?', (user_id,))
        stat_value = cursor.fetchone()[0]

        if stat_type == 'rounds_won':
            thresholds = {10: 1, 50: 2, 100: 8}
        elif stat_type == 'battles_won':
            thresholds = {1: 3, 10: 4, 25:5, 50:6, 100:8}

        for threshold, achievement_id in thresholds.items():
            if stat_value == threshold:
                cursor.execute('''
                INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)
                ''', (user_id, achievement_id))
                conn.commit()

                cursor.execute('SELECT title, description FROM achievements WHERE achievement_id = ?', (achievement_id,))
                achievement = cursor.fetchone()

                try:
                    user = await interaction.client.fetch_user(user_id)
                    if user is not None:
                        embed = discord.Embed(
                            title="Achievement Unlocked!",
                            description=f"{user.mention} unlocked **{achievement[0]}**: {achievement[1]}"

                        )
                        await interaction.channel.send(content=f"{user.mention}", embed=embed)
                    else:
                        print(f"User with ID {user_id} not found.")
                except discord.NotFound:
                    print(f"User with ID {user_id} not found.")
        
        conn.close()





    def compare_stats(self, stat1, stat2, player1, player2):
        if stat1 > stat2:
            self.player1_wins += 1
            return player1
        elif stat1 < stat2:
            self.player2_wins += 1
            return player2
        return None



battles = {}

class DeckSelect(Select):
    def __init__(self, user_id, user, callback):
        self.user_id = user_id
        self.callback_func = callback
        cursor.execute('SELECT deck_name FROM decks WHERE user_id = ?', (user_id,))
        decks = cursor.fetchall()
        options = [discord.SelectOption(label=deck[0], description=f"{user}'s deck") for deck in decks]
        super().__init__(placeholder='Select a deck...', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        deck_name = self.values[0]
        await self.callback_func(interaction.user, deck_name, interaction)

class DeckSelectView(View):
    def __init__(self, user_id, user, callback):
        super().__init__()
        self.add_item(DeckSelect(user_id, user, callback))

class BattleButton(Button):
    def __init__(self, label, user1, user2, battle, action):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.user1 = user1
        self.user2 = user2
        self.battle = battle
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        print(f"[LOG] {interaction.user.name} clicked {self.action} button.")
        
        if interaction.user != self.battle.turn:
            await interaction.response.send_message(f"It's not your turn!", ephemeral=True)
            print(f"[LOG] {interaction.user.name} tried to play out of turn.")
            return

        if interaction.user == self.battle.player1:
            self.battle.player1_action = self.action
            print(f"[LOG] {self.battle.player1.name} action set to {self.battle.player1_action}")
            if self.action == 'attack':
                self.battle.player2_action = 'defense'
            elif self.action == 'defense':
                self.battle.player2_action = 'attack'
            else:
                self.battle.player2_action = 'speed'
            action_msg = (f"**{self.battle.player1.name}** chose **{self.battle.player1_action}**. "
                          f"**{self.battle.player2.name}** will counter with **{self.battle.player2_action}**.")
        else:
            self.battle.player2_action = self.action
            print(f"[LOG] {self.battle.player2.name} action set to {self.battle.player2_action}")
            if self.action == 'attack':
                self.battle.player1_action = 'defense'
            elif self.action == 'defense':
                self.battle.player1_action = 'attack'
            else:
                self.battle.player1_action = 'speed'
            action_msg = (f"**{self.battle.player2.name}** chose **{self.battle.player2_action}**. "
                          f"**{self.battle.player1.name}** will counter with **{self.battle.player1_action}**.")

        embed = discord.Embed(title="Action Selection Phase", description=action_msg)
        await interaction.channel.send(embed=embed)

        # Both players need to select their cards now
        card_select_view = CardSelectView(self.battle.player1, self.battle.player2, self.battle, self.battle.player1_action, self.battle.player2_action)
        embed = discord.Embed(title="Card Selection Phase", description="Both players, select a card from your deck to play.")
        await interaction.channel.send(embed=embed, view=card_select_view)





class CardSelect(Select):
    def __init__(self, player, opponent, battle, player_action, opponent_action):
        self.player = player
        self.opponent = opponent
        self.battle = battle
        self.player_action = player_action
        self.opponent_action = opponent_action

        options = [discord.SelectOption(label=card.name, description=f"ID: {card.card_id}") for card in battle.get_deck(player)]
        super().__init__(placeholder='Select a card...', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        # Check if the interaction is from the correct user
        if interaction.user != self.player:
            await interaction.response.send_message("You are not allowed to select this card.", ephemeral=True)
            return

        card_name = self.values[0]
        card = next(card for card in self.battle.get_deck(self.player) if card.name == card_name)
        print(f"[LOG] {self.player.name} selected {card.name} for {self.player_action}.")

        if self.player == self.battle.player1:
            self.battle.player1_card = card
            print(f"[LOG] Player 1 Card set: {card.name} - Attack: {card.attack}, Defense: {card.defense}, Speed: {card.speed}")
        else:
            self.battle.player2_card = card
            print(f"[LOG] Player 2 Card set: {card.name} - Attack: {card.attack}, Defense: {card.defense}, Speed: {card.speed}")

        log_embed = discord.Embed(title="Card Selection Log", description=f"{self.player.name} selected {card.name}.")
        await interaction.response.send_message(embed=log_embed, ephemeral=True)

        # Check if both players have selected their cards
        if hasattr(self.battle, 'player1_card') and hasattr(self.battle, 'player2_card'):
            await self.battle.resolve_battle(interaction)
        else:
            # Prompt the other player to select their card
            action_msg = (f"**{self.opponent.name}**, please select your card to counter **{self.player.name}**'s **{self.player_action}**.")
            card_select_view = CardSelectView(self.opponent, self.player, self.battle, self.opponent_action, self.player_action)
            embed = discord.Embed(title=f"{self.opponent.name}, select your card", description=action_msg)
            await interaction.channel.send(embed=embed, view=card_select_view)





class CardSelectView(View):
    def __init__(self, player, opponent, battle, player_action, opponent_action):
        super().__init__()
        self.add_item(CardSelect(player, opponent, battle, player_action, opponent_action))

    async def next_round(self, interaction):
        battle = self.battle
        print(f"[LOG] Starting round {battle.round} with {battle.turn.name}'s turn.")
        embed = discord.Embed(title=f"Round {battle.round}", description=f"{battle.turn.name}'s turn")
        view = View()
        view.add_item(BattleButton(label="Attack", user1=battle.player1, user2=battle.player2, battle=battle, action='attack'))
        view.add_item(BattleButton(label="Defense", user1=battle.player1, user2=battle.player2, battle=battle, action='defense'))
        view.add_item(BattleButton(label="Speed", user1=battle.player1, user2=battle.player2, battle=battle, action='speed'))
        await interaction.channel.send(embed=embed, view=view)





class BattleAcceptButton(Button):
    def __init__(self, challenger, challengee, parent_view):
        super().__init__(label="Accept Battle", style=discord.ButtonStyle.green)
        self.challenger = challenger
        self.challengee = challengee
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.challengee:
            await interaction.response.send_message("You cannot accept this battle.", ephemeral=True)
            return
        
        await interaction.message.edit(view=None)
        await self.start_battle(interaction)

    async def start_battle(self, interaction):
        print(f"[LOG] Starting battle between {self.challenger.name} and {self.challengee.name}.")
        # Set the challenger as player 1 and the other user as player 2
        battle = Battle(self.challenger, self.challengee, [], [], self.parent_view)
        battle.turn = self.challenger  # Challenger always starts first

        async def set_deck(player, deck_name, interaction):
            deck = get_deck(player.id, deck_name)
            print(f"[LOG] {player.name} selected deck {deck_name}.")
            if player == battle.player1:
                battle.player1_deck = deck
            else:
                battle.player2_deck = deck
            
            if battle.player1_deck and battle.player2_deck:
                battles[(self.challenger.id, self.challengee.id)] = battle
                await self.display_decks(interaction, battle)

        embed = discord.Embed(title="Battle Accepted", description=f"{self.challengee.name} accepted the battle! {self.challenger.name} goes first.")
        await interaction.channel.send(embed=embed)

        await interaction.channel.send(f"{self.challenger.name}, select your deck:", view=DeckSelectView(self.challenger.id, self.challenger, set_deck))
        await interaction.channel.send(f"{self.challengee.name}, select your deck:", view=DeckSelectView(self.challengee.id, self.challengee, set_deck))

    async def display_decks(self, interaction, battle):
        # Display Player 1 Deck
        player1_deck = "\n".join([f"**{card.name}** - ID: {card.card_id}, Overall: {card.overall}" for card in battle.player1_deck])
        embed = discord.Embed(title=f"{battle.player1.name}'s Deck", description=player1_deck)
        await interaction.channel.send(embed=embed)
        
        # Display Player 2 Deck
        player2_deck = "\n".join([f"**{card.name}** - ID: {card.card_id}, Overall: {card.overall}" for card in battle.player2_deck])
        embed = discord.Embed(title=f"{battle.player2.name}'s Deck", description=player2_deck)
        await interaction.channel.send(embed=embed)

        await self.start_round(interaction, battle)

    async def start_round(self, interaction, battle):
        embed = discord.Embed(title=f"Round {battle.round}", description=f"{battle.turn.name}'s turn to choose an action")
        view = View()
        view.add_item(BattleButton(label="Attack", user1=battle.player1, user2=battle.player2, battle=battle, action='attack'))
        view.add_item(BattleButton(label="Defense", user1=battle.player1, user2=battle.player2, battle=battle, action='defense'))
        view.add_item(BattleButton(label="Speed", user1=battle.player1, user2=battle.player2, battle=battle, action='speed'))
        await interaction.channel.send(embed=embed, view=view)


class BattleDeclineButton(Button):
    def __init__(self, challenger, challengee):
        super().__init__(label="Decline Battle", style=discord.ButtonStyle.red)
        self.challenger = challenger
        self.challengee = challengee

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.challengee:
            await interaction.response.send_message("You cannot decline this battle.", ephemeral=True)
            return

        await interaction.message.edit(view=None)
        await interaction.channel.send(f"{self.challengee.name} declined the battle.")

class BattleView(View):
    def __init__(self, challenger, challengee):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.challengee = challengee
        self.add_item(BattleAcceptButton(challenger, challengee, self))
        self.add_item(BattleDeclineButton(challenger, challengee))

    async def next_round(self, interaction):
        battle = battles[(self.challenger.id, self.challengee.id)]
        print(f"[LOG] Starting round {battle.round} with {battle.turn.name}'s turn.")
        embed = discord.Embed(title=f"Round {battle.round}", description=f"{battle.turn.name}'s turn")
        view = View()
        view.add_item(BattleButton(label="Attack", user1=battle.player1, user2=battle.player2, battle=battle, action='attack'))
        view.add_item(BattleButton(label="Defense", user1=battle.player1, user2=battle.player2, battle=battle, action='defense'))
        view.add_item(BattleButton(label="Speed", user1=battle.player1, user2=battle.player2, battle=battle, action='speed'))
        await interaction.channel.send(embed=embed, view=view)



@bot.command(name='battle')
async def battle(ctx, user: discord.User):
    ensure_player_exists(ctx.author.id, ctx.author.name)
    ensure_player_exists(user.id, user.name)
    
    embed = discord.Embed(title="Battle Request", description=f"{ctx.author.name} has challenged {user.name} to a battle!")
    await ctx.send(embed=embed, view=BattleView(ctx.author, user))


def get_deck(user_id, deck_name):
    cursor.execute('SELECT cards FROM decks WHERE user_id = ? AND deck_name = ?', (user_id, deck_name))
    result = cursor.fetchone()
    if result is None:
        return None
    
    card_ids = list(map(int, result[0].split(',')))
    cards = []
    for card_id in card_ids:
        cursor.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,))
        card_data = cursor.fetchone()
        if card_data:
            cards.append(Card(*card_data))
    return cards

#---------------------------------------------------------COINS AND SALES-------------------------------------------------------------------------------------

def check_card_ownership(user_id, card_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventories WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    ownership = cursor.fetchone()
    conn.close()
    return ownership is not None


def add_coins(user_id, coins):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET coins = coins + ? WHERE user_id = ?", (coins, user_id))
    conn.commit()
    conn.close()

def remove_card_from_inventory(user_id, card_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventories WHERE user_id = ? AND card_id = ?", (user_id, card_id))
    conn.commit()
    conn.close()

class ConfirmButton(Button):
    def __init__(self, card, user_id, sale_value):
        super().__init__(style=discord.ButtonStyle.green, label="Confirm")
        self.card = card
        self.user_id = user_id
        self.sale_value = sale_value

    async def callback(self, interaction):
        add_coins(self.user_id, self.sale_value)
        remove_card_from_inventory(self.user_id, self.card.card_id)
        
        embed = interaction.message.embeds[0]
        embed.add_field(name="Status", value="Sold", inline=True)
        await interaction.response.edit_message(embed=embed, content="The card has been sold.", view=None)
        logger.info(f'Card {self.card.card_id} sold by user {self.user_id}')

class DeclineButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Decline")

    async def callback(self, interaction):
        await interaction.response.edit_message(content="The sale has been declined.", view=None)


@bot.command(name='sell')
async def sell(ctx, card_id: int):
    card = get_card_by_id(card_id)
    if not card or not check_card_ownership(ctx.author.id, card_id):  # Check if the card exists and belongs to the user
        await ctx.send("You don't own this card.")
        return
    
    # Calculate the sale value
    card_type = card.card_type
    overall = card.overall
    sale_value = 100 if card_type == "standard" else 250 if card_type == "icon" else 0
    sale_value += 50 + ((overall - 70) * 5) if overall >= 70 else 0

    content = f'{ctx.author.mention}, do you want to sell this card for {sale_value} coins?'
    embed = discord.Embed(title="Sell Card")
    embed.add_field(name="Name", value=card.name, inline=True)
    embed.add_field(name="ID", value=card.card_id, inline=True)
    embed.add_field(name="Type", value=card_type, inline=True)
    embed.add_field(name="Overall", value=overall, inline=True)
    embed.add_field(name="Sale Value", value=sale_value, inline=True)
    embed.set_image(url=f"attachment://{card.image_path.split('/')[-1]}")
    
    view = View(timeout=60)
    view.add_item(ConfirmButton(card, ctx.author.id, sale_value))
    view.add_item(DeclineButton())
    
    await ctx.send(content=content, embed=embed, view=view, file=discord.File(card.image_path))


#---------------------------------------------------------PACKS-------------------------------------------------------------------------------------

PACKS = {
    1: {
        "name": "rare_player_pack",
        "display_name": "Rare Player Pack",
        "buyable": True,
        "cost": 1000
    },
    2: {
        "name": "icon_pack",
        "display_name": "Icon Pack",
        "buyable": True,
        "cost": 2500
    },
    3: {
        "name": "tester_pack",
        "display_name": "Tester Pack",
        "buyable": False,
        "cost": 0  # Not buyable, so cost is 0
    }
}



@bot.command(name='shop')
async def shop(ctx):
    embed = discord.Embed(title="Shop", description="Available packs for purchase:\nUse `!buy pack_no` to buy the pack.")
    for pack_id, pack_info in PACKS.items():
        if pack_info["buyable"]:
            embed.add_field(name=pack_info["display_name"], value=f"Pack ID: {pack_id}\nCost: {pack_info['cost']} coins", inline=False)
    await ctx.send(embed=embed)


@bot.command(name='buy')
async def buy(ctx, pack_id: int):
    user_id = ctx.author.id
    
    if pack_id not in PACKS:
        await ctx.send("Invalid pack ID.")
        return

    pack = PACKS[pack_id]
    if pack.get("special", False):  # Prevent buying special packs
        await ctx.send("This pack cannot be bought.")
        return

    pack_name = pack["name"]
    cost = pack["cost"]

    if not has_sufficient_coins(user_id, cost):
        await ctx.send("You don't have enough coins to buy this pack.")
        return
    
    deduct_coins(user_id, cost)
    add_pack_to_user(user_id, pack_name)
    await ctx.send(f"You have bought a {pack['display_name']}.")

@bot.command(name='packs')
async def packs(ctx):
    user_id = ctx.author.id
    user_packs = get_user_packs(user_id)
    
    if not user_packs:
        await ctx.send("You don't have any packs.")
        return
    
    embed = discord.Embed(title=f"{ctx.author.name}'s Packs")
    has_packs = False
    for pack_id, pack in PACKS.items():
        pack_name = pack['name']
        pack_quantity = user_packs.get(pack_name, 0)
        if pack_quantity > 0:
            has_packs = True
            embed.add_field(name=f"{pack['display_name']} (ID: {pack_id})", value=f"Quantity: {pack_quantity}", inline=False)
    
    if not has_packs:
        await ctx.send("You don't have any packs.")
    else:
        await ctx.send(embed=embed)


# Helper functions
def get_user_packs(user_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packs WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return {}

@bot.command(name='givepack')
@commands.has_permissions(administrator=True)
async def give_pack(ctx, user: discord.User, pack_id: int):
    if pack_id not in PACKS:
        await ctx.send("Invalid pack ID.")
        return
    
    if PACKS[pack_id]["buyable"]:
        await ctx.send("This pack can be bought from the shop. Use the shop command to purchase it.")
        return

    add_pack_to_user(user.id, PACKS[pack_id]["name"])
    await ctx.send(f"Given {PACKS[pack_id]['display_name']} to {user.name}.")

def add_pack_to_user(user_id, pack_name):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_packs (user_id, pack_name) VALUES (?, ?)', (user_id, pack_name))
    conn.commit()
    conn.close()


def remove_pack_from_user(user_id, pack_name):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE packs SET {pack_name} = {pack_name} - 1 WHERE user_id = ? AND {pack_name} > 0", (user_id,))
    conn.commit()
    conn.close()

def has_sufficient_coins(user_id, cost):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM players WHERE user_id = ?", (user_id,))
    coins = cursor.fetchone()[0]
    conn.close()
    return coins >= cost

def deduct_coins(user_id, amount):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET coins = coins - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_player_id(username):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM players WHERE name = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def is_duplicate_card(user_id, card_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM inventories WHERE user_id = ? AND card_id = ?', (user_id, card_id))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0


@bot.command(name='open')
async def open(ctx, pack_id: int):
    user_id = ctx.author.id

    if pack_id not in PACKS:
        await ctx.send("Invalid pack ID.")
        return

    pack_name = PACKS[pack_id]["name"]

    user_packs = get_user_packs(user_id)
    if not user_packs or user_packs.get(pack_name, 0) <= 0:
        await ctx.send("You don't own this pack.")
        return

    # Open the pack based on its type
    if pack_id == 1:
        card_obtained = await open_rare_player_pack(ctx, user_id)
    elif pack_id == 2:
        card_obtained = await open_icon_pack(ctx, user_id)
    elif pack_id == 3:
        card_obtained = await open_tester_pack(ctx, user_id)

    remove_pack_from_user(user_id, pack_name)
    await ctx.send(f"You have opened a {PACKS[pack_id]['display_name']} and obtained {card_obtained}.")



async def open_rare_player_pack(ctx, user_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()

    card = None
    while True:
        # Define the card types and their respective probabilities
        card_types = ['Standard', 'Other']
        probabilities = [0.8, 0.2]

        # Choose a card type based on the defined probabilities
        chosen_type = random.choices(card_types, probabilities)[0]

        if chosen_type == 'Standard':
            cursor.execute("SELECT card_id, name, card_rarity, card_type, attack, defense, speed, overall, league, nation, image_path FROM cards WHERE card_type = 'Standard' AND overall > 85 ORDER BY RANDOM() LIMIT 1")
        else:
            cursor.execute("SELECT card_id, name, card_rarity, card_type, attack, defense, speed, overall, league, nation, image_path FROM cards WHERE card_type != 'Standard' AND overall > 85 ORDER BY RANDOM() LIMIT 1")

        card = cursor.fetchone()

        if card and not is_duplicate_card(user_id, card[0]):
            break

    card_id, name, rarity, card_type, attack, defense, speed, overall, league, nation, image_path = card

    # Increment the copies attribute of the chosen card
    cursor.execute('UPDATE cards SET copies = copies + 1 WHERE card_id = ?', (card_id,))
    conn.commit()

    # Add the card to the user's inventory
    add_card_to_inventory(user_id, card_id)
    conn.close()

    embed = discord.Embed(title="You have received a card!", description=f"**{name}**")
    embed.set_image(url=f"attachment://{image_path.split('/')[-1]}")
    embed.add_field(name="Rarity", value=rarity, inline=True)
    embed.add_field(name="Type", value=card_type, inline=True)
    embed.add_field(name="Attack", value=attack, inline=True)
    embed.add_field(name="Defense", value=defense, inline=True)
    embed.add_field(name="Speed", value=speed, inline=True)
    embed.add_field(name="Overall", value=overall, inline=True)
    embed.add_field(name="League", value=league, inline=True)
    embed.add_field(name="Nation", value=nation, inline=True)
    embed.add_field(name="Copies", value=1, inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    file = discord.File(image_path, filename=image_path.split('/')[-1])
    await ctx.send(embed=embed, file=file)
    return name



async def open_icon_pack(ctx, user_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()

    card = None
    while True:
        cursor.execute("SELECT card_id, name, card_rarity, card_type, attack, defense, speed, overall, league, nation, image_path FROM cards WHERE card_type = 'Icon' ORDER BY RANDOM() LIMIT 1")
        card = cursor.fetchone()

        if card and not is_duplicate_card(user_id, card[0]):
            break

    card_id, name, rarity, card_type, attack, defense, speed, overall, league, nation, image_path = card

    # Increment the copies attribute of the chosen card
    cursor.execute('UPDATE cards SET copies = copies + 1 WHERE card_id = ?', (card_id,))
    conn.commit()

    # Add the card to the user's inventory
    add_card_to_inventory(user_id, card_id)
    conn.close()

    embed = discord.Embed(title="You have received a card!", description=f"**{name}**")
    embed.set_image(url=f"attachment://{image_path.split('/')[-1]}")
    embed.add_field(name="Rarity", value=rarity, inline=True)
    embed.add_field(name="Type", value=card_type, inline=True)
    embed.add_field(name="Attack", value=attack, inline=True)
    embed.add_field(name="Defense", value=defense, inline=True)
    embed.add_field(name="Speed", value=speed, inline=True)
    embed.add_field(name="Overall", value=overall, inline=True)
    embed.add_field(name="League", value=league, inline=True)
    embed.add_field(name="Nation", value=nation, inline=True)
    embed.add_field(name="Copies", value=1, inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    file = discord.File(image_path, filename=image_path.split('/')[-1])
    await ctx.send(embed=embed, file=file)
    return name



async def open_tester_pack(ctx, user_id):
    conn = sqlite3.connect('cards_game.db')
    cursor = conn.cursor()

    icon_card = None
    while True:
        cursor.execute("SELECT card_id, name, card_rarity, card_type, attack, defense, speed, overall, league, nation, image_path FROM cards WHERE card_type = 'Icon' ORDER BY RANDOM() LIMIT 1")
        icon_card = cursor.fetchone()

        if icon_card and not is_duplicate_card(user_id, icon_card[0]):
            break

    high_overall_cards = []
    while len(high_overall_cards) < 4:
        card_types = ['Standard', 'Other']
        probabilities = [0.9, 0.1]

        chosen_type = random.choices(card_types, probabilities)[0]

        if chosen_type == 'Standard':
            cursor.execute("SELECT card_id, name, card_rarity, card_type, attack, defense, speed, overall, league, nation, image_path FROM cards WHERE card_type = 'Standard' AND overall > 85 ORDER BY RANDOM() LIMIT 1")
        else:
            cursor.execute("SELECT card_id, name, card_rarity, card_type, attack, defense, speed, overall, league, nation, image_path FROM cards WHERE card_type != 'Standard' AND overall > 85 ORDER BY RANDOM() LIMIT 1")

        card = cursor.fetchone()

        if card and not is_duplicate_card(user_id, card[0]):
            high_overall_cards.append(card)

    icon_card_id, icon_name, icon_rarity, icon_card_type, icon_attack, icon_defense, icon_speed, icon_overall, icon_league, icon_nation, icon_image_path = icon_card

    cursor.execute('UPDATE cards SET copies = copies + 1 WHERE card_id = ?', (icon_card_id,))
    conn.commit()
    add_card_to_inventory(user_id, icon_card_id)

    for card in high_overall_cards:
        card_id, name, rarity, card_type, attack, defense, speed, overall, league, nation, image_path = card
        cursor.execute('UPDATE cards SET copies = copies + 1 WHERE card_id = ?', (card_id,))
        conn.commit()
        add_card_to_inventory(user_id, card_id)

    conn.close()

    embed = discord.Embed(title="You have received a Tester Pack!", description=f"**Icon Card: {icon_name}**")
    embed.set_image(url=f"attachment://{icon_image_path.split('/')[-1]}")
    embed.add_field(name="Rarity", value=icon_rarity, inline=True)
    embed.add_field(name="Type", value=icon_card_type, inline=True)
    embed.add_field(name="Attack", value=icon_attack, inline=True)
    embed.add_field(name="Defense", value=icon_defense, inline=True)
    embed.add_field(name="Speed", value=icon_speed, inline=True)
    embed.add_field(name="Overall", value=icon_overall, inline=True)
    embed.add_field(name="League", value=icon_league, inline=True)
    embed.add_field(name="Nation", value=icon_nation, inline=True)
    embed.add_field(name="Copies", value=1, inline=True)

    card_names = [f"{card[0]}: {card[1]}" for card in high_overall_cards]
    await ctx.send(embed=embed, file=discord.File(icon_image_path, filename=icon_image_path.split('/')[-1]))
    await ctx.send(f"Other cards obtained: {', '.join(card_names)}")

    return "5 Cards"



bot.run('MTI1NTUyMDczMjU3MDU4MzA0MA.Gd1CJM.PWHTPnNSdspcvKb8sN69xRbfDLFKuQiUHrgLuY')
