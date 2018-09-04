import Data
import telebot
import config

analytics_main = Data.Database(Data.analytics_db.main)
members_analytics = Data.Database(Data.analytics_db.members)
channels_analytics = Data.analytics_db.channels

users = Data.Database(Data.users_db.users)
members = Data.Database(Data.users_db.members)
channels = Data.Database(Data.channels_db.channels)
halks_channels = channels.search({'channel_creator.username': '@MrHalk'})
ch_list = [halks_channels[i: i + 4] for i in range(0, len(halks_channels), 4)]

files_main = Data.Database(Data.files_db.files_main)
files = Data.Database(Data.files_db.files)
drafts = Data.Database(Data.files_db.drafts)
queued = Data.Database(Data.files_db.queue)
reactions = Data.Database(Data.files_db.reactions)


def main_menu_admin(member_id):

    member = members.get({'user_id': member_id})
    if member is None:
        return None

    # Dummy
    icount = 0
    for message in member['inbox']:
        if not message['read']:
            icount += 1

    if icount > 0:
        inbox = "📫 My Inbox (%d)" % icount
    else:
        inbox = "📫 My Inbox"

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)

    uchannels = telebot.types.KeyboardButton("🖊 Manage Channels")
    # usettings = telebot.types.KeyboardButton("⚙️ Settings")
    unpost = telebot.types.KeyboardButton("📝 New Post")
    uinbox = telebot.types.KeyboardButton(inbox)
    uposts = telebot.types.KeyboardButton("🗄 My Posts")

    kb.row(unpost, uinbox)
    kb.row(uposts,)  # usettings)
    kb.add(uchannels)

    return kb


def main_menu_post_options(m, gl):
    cid = m.chat.id
    globs = gl.create_post[cid]
    if globs.default_silenced:
        silenced_txt = '✅'
        silenced_data = 'post_options=True silence_posts=disable'
    else:
        silenced_txt = '☑'
        silenced_data = 'post_options=True silence_posts=enable'

    if globs.disable_web_page_preview:
        link_preview_txt = '☑'
        link_preview_data = 'post_options=True web_preview=enable'
    else:
        link_preview_txt = '✅'
        link_preview_data = 'post_options=True web_preview=disable'

    if globs.default_caption is None:
        default_caption_txt = "✏ Set a Default Caption"
        default_caption_data = 'post_options=True default_caption=set'
    else:
        default_caption_txt = "📝 Edit the Default Caption"
        default_caption_data = 'post_options=True default_caption=edit'

    if globs.reactions is None:
        default_reaction_text = '😂 Set Default Reactions'
        default_reaction_data = 'post_options=True default_reactions=set'
    else:
        default_reaction_text = '👌 Edit the Default Reactions'
        default_reaction_data = 'post_options=True default_reactions=edit'
    kb = telebot.types.InlineKeyboardMarkup(row_width=4)
    b_all_silenced = telebot.types.InlineKeyboardButton("🔔 Silenced Posts:",
                                                        callback_data='post_options=True silence_posts=True')
    all_silenced = telebot.types.InlineKeyboardButton(silenced_txt, callback_data=silenced_data)
    b_link_preview = telebot.types.InlineKeyboardButton("📎 Link Previews:",
                                                        callback_data='post_options=True web_preview=True')
    link_preview = telebot.types.InlineKeyboardButton(link_preview_txt, callback_data=link_preview_data)
    default_caption = telebot.types.InlineKeyboardButton(default_caption_txt,
                                                         callback_data=default_caption_data)
    default_reaction = telebot.types.InlineKeyboardButton(default_reaction_text,
                                                          callback_data=default_reaction_data)

    kb.row(b_all_silenced, all_silenced)
    kb.row(b_link_preview, link_preview)
    kb.add(default_caption)
    kb.add(default_reaction)
    if gl.create_post[cid].channel in config.CHANNELS:
        if 'zig_zag' not in gl.create_post[cid]:
            gl.create_post[cid].zig_zag = False

        if gl.create_post[cid].zig_zag:
            zz_txt = "Remove Zig-Zag Line"
            zz_call = 'post_options=True zig_zag=disable'
        else:
            zz_txt = "Include Zig-Zag Line"
            zz_call = 'post_options=True zig_zag=enable'
        zig_zag = telebot.types.InlineKeyboardButton(zz_txt, callback_data=zz_call)
        kb.add(zig_zag)
    return kb
