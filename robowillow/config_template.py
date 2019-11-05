"""RoboWillow config template, shoule be renamed to config.py before use."""

# bot token from discord developers
bot_token = 'your_token_here'

# default bot settings
bot_prefix = '!'
bot_owner = 12345678903216549878
bot_coowners = []
preload_extensions = []
version = '0'

# minimum required permissions for bot user
bot_permissions = 268822736
bot_status = "with maps at site.com"

# mongodb database credentials
db_details = {
    'username': 'willow',
    'database': 'willow',
    'hostname': 'localhost',
    'password': 'password'
}

file_paths = {
    'map_directory': '/var/www/html/maps/',
    'tasklist': './tasklist.pkl'
}

# default language
lang_bot = 'en'
lang_pkmn = 'en'

# help command categories (stole from meowth, not sure if I want to keep yet)
command_categories = {
    "Owner": {
        "index": "5",
        "description": "Owner-only commands for bot config or info."
    },
    "Server Config": {
        "index": "10",
        "description": "Server configuration commands."
    },
    "Bot Info": {
        "index": "15",
        "description": "Commands for finding out information on the bot."
    },
}
