"""Main runner for robowillow."""
import discord
import asyncio
import sys
from robowillow.core import Bot


def run_bot(debug=False):
    """Set up the bot, run it and handle exit codes."""
    bot = Bot(debug=debug)

    # create async loop and setup contextvar
    loop = asyncio.get_event_loop()

    bot.load_extension("robowillow.core.core_commands")
    bot.load_extension("robowillow.exts.mapping")
    bot.load_extension("robowillow.exts.trade")

    if bot.token is None or not bot.default_prefix:
        bot.logger.critical("Token and prefix must be set in order to login.")
        print("Token and prefix must be set in order to login.")
        sys.exit(1)

    try:
        loop.run_until_complete(bot.start(bot.token))
    except discord.LoginFailure:
        bot.logger.critical("Invalid token")
        loop.run_until_complete(bot.logout())
    except KeyboardInterrupt:
        bot.logger.info("Keyboard interrupt detected. Quitting...")
        loop.run_until_complete(bot.logout())
    except Exception as exc:
        bot.logger.critical("Fatal exception", exc_info=exc)
        loop.run_until_complete(bot.logout())
    finally:
        sys.exit(1)


def main():
    """Run the bot."""
    run_bot(debug=True)


if __name__ == '__main__':
    main()