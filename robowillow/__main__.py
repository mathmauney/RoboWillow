import discord
import sys
from .core import Bot


def run_bot(debug=False):
    """Sets up the bot, runs it and handles exit codes."""

    bot = Bot(debug=debug)

    bot.load_extension("robowillow.exts.mapping")
    bot.load_extension("robowillow.core")

    if bot.token is None or not bot.default_prefix:
        bot.logger.critical(
            "Token and prefix must be set in order to login.")
        sys.exit(1)


def main():
    run_bot(debug=True)


if __name__ == '__main__':
    main()
