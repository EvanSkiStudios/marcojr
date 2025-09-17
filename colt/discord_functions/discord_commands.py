import discord


def discord_activity_mapper(activity):
    activity_type_map = {
        discord.ActivityType.playing: "playing",
        discord.ActivityType.streaming: "streaming",
        discord.ActivityType.listening: "listening to",
        discord.ActivityType.watching: "watching",
        discord.ActivityType.competing: "competing in",
        discord.ActivityType.custom: "Custom"
    }
    return activity_type_map.get(activity.type, f"Unknown({activity.type.name.lower()})")


async def command_status(client, ctx, arg):
    print(f"Command issued: Status")

    # set the status to custom if supplied otherwise get a random one from the list in set_activity
    if arg is not None:
        # max character limit
        arg = arg[:128]
        activity = discord.CustomActivity(name=f"{arg}", emoji=' ')
        await client.change_presence(activity=activity)
    else:
        activity = None
        await client.change_presence(activity=activity)

    # Get the new activity to respond with the new info about the status
    if activity is not None:
        if activity.type == discord.ActivityType.custom:
            await ctx.send(f"Custom Status is now: {activity.name}")
        else:
            await ctx.send(f"Status is now: {discord_activity_mapper(activity)} {activity.name}")
    else:
        await ctx.send("Status has been cleared.")
        print("Status Cleared")
        return

    print(f"Changed Status to: {activity.type} {activity.name}")


async def command_delete(client, ctx, arg):
    messages = arg.split(',')

    deleted = []
    failed = []

    for msg_id in messages:
        try:
            msg_id = int(msg_id)
            msg = await ctx.channel.fetch_message(msg_id)
            if msg.author == client.user:
                await msg.delete()
                deleted.append(msg_id)
            else:
                failed.append((msg_id, "Not sent by bot"))
        except discord.NotFound:
            failed.append((msg_id, "Message not found"))
        except discord.Forbidden:
            failed.append((msg_id, "Missing permissions"))
        except discord.HTTPException as e:
            failed.append((msg_id, f"HTTP error: {e}"))

    report = []
    if deleted:
        report.append(f"✅ Deleted: {', '.join(map(str, deleted))}")
    if failed:
        report.append("❌ Failed:\n" + "\n".join(f"{i}: {reason}" for i, reason in failed))

    print(report)
    msg = await ctx.send("Deleted: (" + str(len(deleted)) + ") Messages", delete_after=6)
    # colt_current_session_chat_cache.clear()
    # await ctx.send(
    #    "https://tenor.com/view/men-in-black-mib-will-smith-u-saw-nothing-kharter-gif-12731469441707899432",
    #    delete_after=5, reference=msg
    # )


