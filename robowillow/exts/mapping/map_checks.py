from discord.ext.commands import check

async def is_map_channel(ctx):
    table = ctx.bot.dbi.table('report_channels')
    query = table.query('meetup')
    query.where(channelid=ctx.channel.id)
    meetup = await query.get_value()
    if not meetup:
        raise MeetupDisabled
    else:
        return True

def map_channel():
    return check(is_map_channel)
