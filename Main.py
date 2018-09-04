import telebot
import sys
import logging
# import random
import gc
import datetime
import time
import os  # , urllib
import Data
import config
import utils
import TempCache
from bot_utils import preview_posts, message_user
import logger as lg
from aiohttp import web
from importlib import reload
import components

# import ssl2647
WEBHOOK_HOST = 'halksnet.westeurope.cloudapp.azure.com'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = 'etc/cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = 'etc/key.pem'  # Path to the ssl private key

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(config.BOT_TOKEN)

gc.enable()

# Main BOT
bot = telebot.AsyncTeleBot(config.BOT_TOKEN, num_threads=16)
# LOGGERS
telebot_logger = telebot.logger  # set logger
if config.DEV:
    telebot_logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.
else:
    telebot_logger.setLevel(logging.INFO)
# Main Logger
logger = lg.logger
# END OF LOGS

# START OF DBs
analytics_main = Data.Database(Data.analytics_db.main)
members_analytics = Data.Database(Data.analytics_db.members)
channels_analytics = Data.Database(Data.analytics_db.channels)

users = Data.Database(Data.users_db.users)
members = Data.Database(Data.users_db.members)
channels = Data.Database(Data.channels_db.channels)
# halks_channels = channels.search({})
# ch_list = [halks_channels[i: i + 6] for i in range(0, len(halks_channels), 6)]
ch_list = config.ch_list

files_main = Data.Database(Data.files_db.files_main)
files = Data.Database(Data.files_db.files)
drafts = Data.Database(Data.files_db.drafts)
queued = Data.Database(Data.files_db.queue)
reactions = Data.Database(Data.files_db.reactions)
# END OF DBs

# START OF CACHES
reactions_cache = TempCache.reactions_cache
deep_link_cache = TempCache.deep_link_cache
GLOBAL = utils.Dictionary({'create_post': {}})
master_id = config.BOT_SUDO
# END OF CACHES


# Listener to see when new messages arrives
def listener(messages):
    # When new messages arrive TeleBot will call this function.

    for m in messages:
        if m.content_type == 'text':
            # Print the sent message to the console
            print(str(m.chat.first_name) + '[' + str(m.from_user.id) + ']: ' + m.text)
        print(m)
        # print(files.search({'message_id': m.message_id}))

# bot.set_update_listener(listener)  # register listener


app = web.Application()


# Process webhook calls
async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)

app.router.add_post('/{token}/', handle)


def deep_link_handler(m, call):
    dl = deep_link_cache.read(call)
    safe = m
    copy_name = safe.from_user.first_name
    if dl is not None:
        if dl['call'] == 'add_admin':
            channel = channels.get({'channel_id': dl['channel']})
            member = members.get({'user_id': m.chat.id})
            if member is not None:
                if channel['channel_id'] in member['authorized_channels']:
                    return bot.send_message(chat_id=m.chat.id,
                                            text="You're already authorized to post in %s !" % channel['channel_name'])

                elif channel['channel_id'] in member['owned_channels']:
                    return bot.send_message(chat_id=m.chat.id,
                                            text="You own %s !" % channel['channel_name'])
                members.update({'user_id': m.chat.id}, {'$addToSet': {'authorized_channels': channel['channel_id']}})
            else:
                data = {
                    'user_id': m.from_user.id,
                    'user_username': m.from_user.username,
                    'user_name': m.from_user.first_name,
                    'owned_channels': [],
                    'authorized_channels': [channel['channel_id']],
                    'inbox': [],
                    'feedbacks': [],
                    'queue_posts': [],
                    'drafts': [],
                    'posts': []
                }
                analytics_data = {'user_id': m.chat.id, 'all_time_posts': 0, 'posts': []}

                members.write(data)
                members_analytics.write(analytics_data)
                welcome_text = 'Welcome to *Hαlk\'s Eastern Media Network*!\n\n' \
                               'We\'re so happy you\'re helping us! Feel like home here.\n' \
                               'If anything, contact @MrHalk 😉'
                data = {'type': 'text',
                        'caption': None,
                        'file_id': None,
                        'text': welcome_text,
                        'title': 'Welcome!'}
                member_id = m.chat.id
                m.from_user.first_name = 'SYSADMIN'
                m.from_user.username = None
                m.from_user.id = None
                message_user(bot, safe, GLOBAL, data, member_id, members)

            text = "%s is now admin at %s" % (copy_name, channel['channel_name'])
            bot.send_message(chat_id=channel['channel_creator']['id'], text=text)
            kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
            bot.send_message(chat_id=m.chat.id, text="You're now admin at %s" % channel['channel_name'],
                             reply_markup=kb)

        elif dl['call'] == 'add_networker':
            member = members.get({'user_id': m.chat.id})
            if member is not None:
                return bot.send_message(chat_id=m.chat.id, text="You're already registered!")

            data = {
                'user_id': m.from_user.id,
                'user_username': m.from_user.username,
                'user_name': m.from_user.first_name,
                'owned_channels': [],
                'authorized_channels': [],
                'inbox': [],
                'feedbacks': [],
                'queue_posts': [],
                'drafts': [],
                'posts': []
            }
            analytics_data = {'user_id': m.chat.id, 'all_time_posts': 0, 'posts': []}

            members.write(data)
            members_analytics.write(analytics_data)

            welcome_text = 'Welcome to *Hαlk\'s Eastern Media Network*!\n\n' \
                           'We\'re so happy you\'re helping us! Feel like home here.\n' \
                           'If anything, contact @MrHalk 😉'
            data = {'type': 'text',
                    'caption': None,
                    'file_id': None,
                    'text': welcome_text,
                    'title': 'Welcome!'}
            member_id = m.chat.id

            kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
            bot.send_message(chat_id=m.chat.id, text="Welcome home *%s*\n\n"
                                                     "Use the buttons below to, you know, "
                                                     "~do your stunt~." % m.from_user.first_name.replace('_', '\_').
                             replace('*', '\*').replace('`', '\`'),
                             reply_markup=kb, parse_mode='markdown').wait()

            safe.from_user.first_name = 'SYSADMIN'
            safe.from_user.username = None
            safe.from_user.id = None
            message_user(bot, safe, GLOBAL, data, member_id, members)

    else:
        txt = 'Error: Deep Link doesn\'t exist.'
        bot.send_message(m.chat.id, txt)

    return


"""@bot.channel_post_handler()
def channel_handler(m):
    cid = m.chat.id
    mid = m.message_id
    string = utils.str_generator(12)
    try:
        post_quantity = files_main.get({'_id': config.FILES_MAIN})['created_posts']

        sid = utils.id_encoder(post_quantity + 1)

        caption = m.caption

        # This variable is to tell if the post was made or not. Default to False, due to the last if.
        f = False

        if m.content_type == 'photo':
            post = utils.Dictionary({'id': sid,
                                     'creator': cid,
                                                  'string': string,
                                                  'type': 'photo',
                                                  'height': m.photo[len(m.photo) - 1].height,
                                                  'width': m.photo[len(m.photo) - 1].width,
                                                  'file_id': m.photo[len(m.photo) - 1].file_id,
                                                  'caption': caption,
                                                  'tags': [],
                                                  'disable_notif': False,
                                                  'custom_reactions': {'preview': None,
                                                                       'reactions': reaction},
                                                  'channel': gl.create_post[cid].channel
                                                  }
                                                 )

            if caption is not None:
                try:
                    make_sauce(caption, post_list[string])
                except AttributeError:
                    # This means we couldn't make a sauce
                    pass
                except Exception as e:
                    raise e

            fetch_tags(cid, gl, caption, string)

        elif m.content_type == 'text':
            try:
                s = bot.send_message(config.PHOTOS_CHANNEL, m.text, parse_mode='markdown').wait()
                if isinstance(s, tuple):
                    raise s[1]
                post_list[string] = utils.Dictionary({'id': sid,
                                                      'creator': cid,
                                                      'string': string,
                                                      'type': 'text',
                                                      'text': m.text,
                                                      'tags': [],
                                                      'disable_notif': False,
                                                      'custom_reactions': {'preview': None,
                                                                           'reactions': reaction},
                                                      'channel': gl.create_post[cid].channel
                                                      }
                                                     )

                fetch_tags(cid, gl, m.text, string)

            except Exception as e:
                print(e)
                text = 'Error in the markdown formatting.\n' \
                       'Check your text and try again.'

                return bot.send_message(cid, text)

        elif m.content_type == 'document':
            post_list[string] = utils.Dictionary({'id': sid,
                                                  'creator': cid,
                                                  'string': string,
                                                  'type': 'document',
                                                  'file_id': m.document.file_id,
                                                  'mime_type': m.document.mime_type,
                                                  'caption': caption,
                                                  'tags': [],
                                                  'disable_notif': False,
                                                  'custom_reactions': {'preview': None,
                                                                       'reactions': reaction},
                                                  'channel': gl.create_post[cid].channel
                                                  }
                                                 )
            fetch_tags(cid, gl, caption, string)

        elif m.content_type == 'video':
            post_list[string] = utils.Dictionary({'id': sid,
                                                  'creator': cid,
                                                  'string': string,
                                                  'type': 'video',
                                                  'width': m.video.width,
                                                  'height': m.video.height,
                                                  'duration': m.video.duration,
                                                  'caption': caption,
                                                  'tags': [],
                                                  'file_id': m.video.file_id,
                                                  'disable_notif': False,
                                                  'custom_reactions': {'preview': None,
                                                                       'reactions': reaction},
                                                  'channel': gl.create_post[cid].channel
                                                  }
                                                 )
            fetch_tags(cid, gl, caption, string)

        else:
            factor = m.content_type
            bot.send_message(cid, 'Yo fuqr, I won\'t send `{}` to the channel U.U'.format(factor),
                             parse_mode='markdown')

            # In case the post wasn't made due to content_type, f is evaluated to true.
            f = True

        if not f:
            file = [post_list[string]]
            preview_posts(bot, gl, m, file=file)
            files_main.update({'_id': config.FILES_MAIN}, {'$inc': {'created_posts': 1}})
            analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'created_posts': 1}})
            files.write({'id': sid})
    except telebot.apihelper.ApiException:
        if gl.create_post[cid].posts[string].type == 'text':
            text = 'Error in the markdown formatting.\n' \
                   'Check your text and try again.'

            bot.send_message(cid, text)
            del gl.create_post[cid].posts[string]
    except Exception as e:
        report_code = utils.str_generator(6)
        report = "User {0} ({1}) Reported the following issue:\n\n" \
                 "{2}\n\n" \
                 "REPORT CODE: {3}".format(cid, m.from_user.first_name, e, report_code)
        gl.report = utils.Dictionary({report_code: report})
        txt = 'An error occurred while processing your request. Please tap the button below to report it.'
        markup = telebot.types.InlineKeyboardMarkup()
        report_button = telebot.types.InlineKeyboardButton("✉️ Send Report",
                                                           callback_data="report={}".format(report_code))
        markup.add(report_button)
        bot.send_message(cid, txt, reply_markup=markup)
        logger.error(e)"""


@bot.message_handler(commands=['start'])
def start(m):
    cid = m.from_user.id
    tl1 = u'Yo *{name}*.\n\n' \
          u'I am Liliαn, the Light Linear Assistant for Networking, designed to assist all ' \
          u'[👁‍🗨@HαlksNET](t.me/halksnet) channels.\n\n' \
          u'I am for exclusive use of the Network channels, so if you want to join the Network and use me,' \
          u'You shall talk to @MrHalk.'.format(
            name=m.from_user.first_name)
    tl2 = 'Welcome back again *{name}*\n\nUse the buttons below to, you know, ~do your stunt~.'.format(
        name=m.from_user.first_name)

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)

    dl = utils.deep_link(m.text)
    if dl is not None:
        return deep_link_handler(m, dl)

    else:
        staff = [i['user_id'] for i in members.search({})]
        if cid in staff or cid in master_id:
            bot.send_message(cid, tl1, reply_markup=components.callback_kbbuttons.main_menu_admin(cid),
                             parse_mode='markdown')

        else:
            bot.send_message(cid, tl2, reply_markup=kb, parse_mode='markdown')

    return


@bot.message_handler(func=lambda m: "❌ Cancel" in m.text if m.text is not None else None)
@bot.message_handler(commands=['cancel'])
def cancel_op(m):
    cid = m.from_user.id
    txt = "Operation Canceled."

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)

    u1 = telebot.types.KeyboardButton("📣 Feedback")
    u2 = telebot.types.KeyboardButton("❓ Help")
    u3 = telebot.types.KeyboardButton("🌐 Our Channels")
    u4 = telebot.types.KeyboardButton("✉ Contact us!")
    u5 = telebot.types.KeyboardButton("⚜ Bring your channel to 👁‍🗨@HαlksNET! ⚜")

    staff = [i['user_id'] for i in members.search({})]
    if cid in staff or cid in master_id:
        kb = components.callback_kbbuttons.main_menu_admin(cid)

    else:
        kb.add(u4)
        kb.row(u1, u2, u3)
        kb.add(u5)

    bot.send_message(cid, txt, reply_markup=kb)
    if cid in GLOBAL.create_post:
        for post in GLOBAL.create_post[cid].posts:
            files.delete({'id': GLOBAL.create_post[cid].posts[post].id})
        del GLOBAL.create_post[cid]

    if 'edit_channel_info' in GLOBAL:
        if cid in GLOBAL.edit_channel_info:
            del GLOBAL.edit_channel_info[cid]
    if 'add_channel' in GLOBAL:
        if cid in GLOBAL.add_channel:
            del GLOBAL.add_channel[cid]

    return


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] == 'reaction')
def reactions_handler(call):
    return components.reactions.reactions_handler(bot, call, files, reactions, reactions_cache, logger)


@bot.message_handler(func=lambda m: m.text == "🖊 Manage Channels")
@bot.message_handler(commands=['manage'])
def channel_management(m):
    reload(components)
    return components.management.channel_management(bot, m)


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] == 'admin_channel')
def call_channel_management(call):
    reload(components)
    return components.management.call_channel_management(bot, call, GLOBAL, ch_list)


@bot.message_handler(func=lambda m: m.text == "🗄 My Posts")
@bot.message_handler(commands=['my_posts'])
def my_posts(m):
    reload(components)
    return components.posts.my_posts(bot, m)


@bot.message_handler(func=lambda m: m.text is not None and "📫 My Inbox" in m.text)
@bot.message_handler(commands=['my_inbox'])
def my_mail(m):
    reload(components)
    return components.mail.my_inbox(bot, m)


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] == 'my_inbox')
def my_inbox_handler(call):
    return components.mail.my_inbox_handler(bot, call)


@bot.message_handler(func=lambda m: m.text == "🗑 Clear All")
@bot.message_handler(commands=['clear_all', 'delete_all'])
def clear_all(m):
    cid = m.chat.id
    if 'create_post' in GLOBAL:
        if cid in GLOBAL.create_post:
            kb = telebot.types.InlineKeyboardMarkup()
            yes_btn = telebot.types.InlineKeyboardButton("Yes", callback_data='clear_confirm=Yes')
            no_btn = telebot.types.InlineKeyboardButton("No", callback_data='clear_confirm=No')
            kb.row(yes_btn, no_btn)
            txt = 'Are you sure you want to clear all posts you\'ve prepared?\n\n' \
                  '_This action can not be undone._'
            bot.send_message(cid, txt, parse_mode='markdown', reply_markup=kb)

        else:
            txt = "Error: post not cached / missing.\n\n" \
                  "_This error may be caused because the server restarted and lost the cached info in-memory._\n\n" \
                  "Please, try to add your channel again."
            kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
            return bot.send_message(m.chat.id, txt, reply_markup=kb, parse_mode='markdown')
    else:
        txt = "Error: post not cached / missing.\n\n" \
              "_This error may be caused because the server restarted and lost the cached info in-memory._\n\n" \
              "Please, try to add your channel again."
        kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
        return bot.send_message(m.chat.id, txt, reply_markup=kb, parse_mode='markdown')


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] == 'clear_confirm')
def clear_confirm(call):
    splt = call.data.split()[0].split('=')
    cid = call.message.chat.id
    if splt[1] == 'Yes':
        posts = [i for i in GLOBAL.create_post[cid].posts]
        for post in posts:
            files.delete({'id': GLOBAL.create_post[cid].posts[post].id})
            del GLOBAL.create_post[cid].posts[post]

        txt = "Done! All posts removed."
        return bot.edit_message_text(txt, cid, call.message.message_id, call.id)
    elif splt[1] == 'No':
        return bot.answer_callback_query(call.id, "Operation canceled. You can keep sending messages now.")


@bot.message_handler(func=lambda m: m.text == "📝 New Post")
@bot.message_handler(commands=['new_post'])
def new_post(m):
    return components.posts.new_post(bot, m, ch_list)


@bot.message_handler(func=lambda m: m.text == "👁 Preview")
@bot.message_handler(commands=['preview'])
def preview(m):
    try:
        if m.chat.id not in GLOBAL.create_post:
            txt = "Error: post not cached / missing.\n\n" \
                  "_This error may be caused because the server restarted and lost the cached info in-memory._\n\n" \
                  "Please, redo your post."
            kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
            return bot.send_message(m.chat.id, txt, reply_markup=kb, parse_mode='markdown')
        return preview_posts(bot, GLOBAL, m, full_post=True, preview_only=True)
    except Exception as e:
        import traceback
        utils.report_msg(bot, m, GLOBAL, e, str(traceback.format_exc()), msg="Func: preview")
        logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


@bot.message_handler(func=lambda m: m.text == "🚀 Post")
@bot.message_handler(commands=['send'])
def send(m):
    cid = m.from_user.id
    if cid not in GLOBAL.create_post:
        txt = "Error: post not cached / missing.\n\n" \
              "_This error may be caused because the server restarted and lost the cached info in-memory._\n\n" \
              "Please, redo your post."
        kb = components.callback_kbbuttons.main_menu_admin(cid)
        return bot.send_message(cid, txt, reply_markup=kb, parse_mode='markdown')
    kb = telebot.types.InlineKeyboardMarkup(row_width=4)
    # schedule = telebot.types.InlineKeyboardButton("⏱ Schedule", callback_data="schedule_posts=%d" % cid)
    add_queue = telebot.types.InlineKeyboardButton("💤 Add to Queue", callback_data="queue_posts=%d" % cid)
    post = telebot.types.InlineKeyboardButton("🚀 Post Now", callback_data="send_posts=%d" % cid)

    kb.add(post, add_queue)
    # kb.add(schedule, add_queue)

    txt = "Select how we'll proceed with your post."
    bot.send_message(cid, txt, reply_markup=kb)

    return


@bot.message_handler(func=lambda m: m.text == "📋 Options")
@bot.message_handler(commands=['options'])
def options(m):
    reload(components)
    cid = m.chat.id
    if 'create_post' in GLOBAL:
        if cid in GLOBAL.create_post:
            kb = components.callback_kbbuttons.main_menu_post_options(m, GLOBAL)
            txt = 'Here you are the *OPTIONS*.\n\n' \
                  'Use them to customize your posts, and avoid making the same stuff repeatedly.'

            bot.send_message(cid, txt, reply_markup=kb, parse_mode='markdown')
        else:
                txt = "Error: post not cached / missing.\n\n" \
                      "_This error may be caused because the server restarted and lost the cached info " \
                      "in-memory._\n\n" \
                      "Please, try to add your channel again."
                kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
                return bot.send_message(m.chat.id, txt, reply_markup=kb, parse_mode='markdown')
    return


@bot.message_handler(func=lambda m: m.text == "✏ Save Draft")
@bot.message_handler(commands=['draft', 'save_draft'])
def save_as_draft(m):
    cid = m.chat.id
    if m.chat.id not in GLOBAL.create_post:
        txt = "Error: post not cached / missing.\n\n" \
              "_This error may be caused because the server restarted and lost the cached info in-memory._\n\n" \
              "Please, try to add your channel again."
        kb = components.callback_kbbuttons.main_menu_admin(m.chat.id)
        return bot.send_message(m.chat.id, txt, reply_markup=kb, parse_mode='markdown')
    loading = bot.send_message(cid, "🕐 Saving as a draft...")

    new_id = utils.str_generator(12)
    for post in GLOBAL['create_post'][cid]['posts']:
        if 'custom_reactions' in GLOBAL['create_post'][cid]['posts'][post]:
            del GLOBAL['create_post'][cid]['posts'][post]['custom_reactions']['preview']

    drafts.write({'draft_id': new_id,
                  'draft': GLOBAL.create_post[cid],
                  'date': time.mktime(datetime.datetime.utcnow().timetuple())})

    members.update({'user_id': cid}, {'$addToSet': {'drafts': new_id}})

    txt = 'Done. Post saved as a draft.\n\n' \
          'You can continue working on it later, by using the "My Posts" menu.'

    bot.send_message(cid, txt, reply_markup=components.callback_kbbuttons.main_menu_admin(cid))

    return bot.delete_message(cid, loading.wait().message_id)


@bot.message_handler(func=lambda m: m.text == "📣 Feedback")
@bot.message_handler(commands=['feedback'])
def feedback(m):
    cid = m.from_user.id
    if 'feedback' not in GLOBAL:
        GLOBAL.feedback = utils.Dictionary()

    txt = "Okay. You can now write your feedback about our [Network](t.me/halksnet)."
    bts = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    b1 = telebot.types.KeyboardButton("❌ Cancel")
    bts.add(b1)
    bot.send_message(cid, txt, reply_markup=bts, parse_mode='markdown')


@bot.message_handler(commands=['admin'])  # Admin command, for Statistics, and in the future, for broadcasting
def admin(m):
    reload(components)
    return components.admin.admin(bot, m)


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] == 'admin')
def admin_handler(call):
    return components.admin.admin_handler(bot, call, GLOBAL)


# This is the handler for the posts.
@bot.message_handler(content_types=['photo', 'document', 'text', 'video', 'sticker', 'voice', 'location', 'audio'])
def queue_handler(m):
    cid = m.from_user.id
    if m.text is not None and m.text.startswith("/view__"):
        splt = m.text.split("__")
        b = telebot.types.InlineKeyboardMarkup()
        t = telebot.types.InlineKeyboardButton("❌", callback_data='delete_message')
        b.add(t)
        return bot.send_photo(cid, splt[1], reply_to_message_id=m.message_id, reply_markup=b)
    if cid in master_id:
        if 'admin' in GLOBAL:
            if 'add_channel' in GLOBAL.admin:

                kb = telebot.types.InlineKeyboardMarkup(row_width=4)
                save = telebot.types.InlineKeyboardButton("Yes",
                                                          callback_data='admin=channels save_channel=True')
                discard = telebot.types.InlineKeyboardButton("No",
                                                             callback_data='admin=channels discard_channel=True')
                kb.add(save)
                kb.add(discard)

                text = 'Channel Info:' \
                       '*Channel ID*: `{0}`\n' \
                       '*Channel Name:* {1}\n' \
                       '*Channel Info:* \n{2}\n\n' \
                       '*Channel Username:* {3}\n' \
                       '*Channel Link:* {4}\n' \
                       '*Channel Creator:* {5}\n' \
                       '*Channel Profile Pic: {6}*'
                if GLOBAL.admin.add_channel is True:
                    channel_name = m.forward_from_chat.title
                    channel_id = m.forward_from_chat.id
                    username = '@' + m.forward_from_chat.username if m.forward_from_chat.username is not None else None
                    GLOBAL.admin.new_channel_info.channel_name = channel_name
                    GLOBAL.admin.new_channel_info.channel_username = username
                    GLOBAL.admin.new_channel_info.channel_id = channel_id
                    GLOBAL.admin.new_channel_info.channel_profile_pic = \
                        m.photo[len(m.photo) - 1].file_id if m.photo is not None else "None"
                    text = text.format(
                        GLOBAL.admin.new_channel_info.channel_id,
                        GLOBAL.admin.new_channel_info.channel_name,
                        GLOBAL.admin.new_channel_info.channel_info,
                        GLOBAL.admin.new_channel_info.channel_username,
                        GLOBAL.admin.new_channel_info.channel_private_link,
                        '{0} {1}'.format(
                            GLOBAL.admin.new_channel_info.channel_creator.name,
                            GLOBAL.admin.new_channel_info.channel_creator.username
                        ),
                        "/view__" + GLOBAL.admin.new_channel_info.channel_profile_pic
                    ).replace("_", "\_")

                    bot.send_message(cid, text, reply_markup=kb, parse_mode='markdown')
                    del GLOBAL.admin.add_channel

        elif 'send_admin_message' in GLOBAL:
            if GLOBAL.send_admin_message.queue == 'title':
                if m.content_type == 'text':
                    GLOBAL.send_admin_message.message.title = m.text
                    GLOBAL.send_admin_message.queue = 'message'

                    return bot.send_message(chat_id=cid, text='Now, send the message')
            elif GLOBAL.send_admin_message.queue == 'message':
                if m.content_type == 'photo':
                    GLOBAL.send_admin_message.message.type = 'photo'
                    GLOBAL.send_admin_message.message.caption = m.caption
                    GLOBAL.send_admin_message.message.file_id = m.photo[len(m.photo) - 1].file_id
                elif m.content_type == 'text':
                    GLOBAL.send_admin_message.message.type = 'text'
                    GLOBAL.send_admin_message.message.text = m.text
                elif m.content_type == 'document':
                    GLOBAL.send_admin_message.message.type = 'document'
                    GLOBAL.send_admin_message.message.caption = m.caption
                    GLOBAL.send_admin_message.message.file_id = m.document.file_id
                elif m.content_type == 'video':
                    GLOBAL.send_admin_message.message.type = 'video'
                    GLOBAL.send_admin_message.message.caption = m.caption
                    GLOBAL.send_admin_message.message.file_id = m.video.file_id

                all_members = members.search({})
                for member in all_members:
                    member_id = member['user_id']
                    m.from_user.first_name = 'SYSADMIN'
                    m.from_user.username = None
                    m.from_user.id = None
                    message_user(bot, m, GLOBAL, GLOBAL.send_admin_message.message, member_id, members)
                del GLOBAL.send_admin_message
                return

    if 'edit_channel_info' in GLOBAL:
        if cid in GLOBAL.edit_channel_info:
            from components.management import edit_info_channel_management
            return edit_info_channel_management(bot, m, GLOBAL)

    if 'add_channel' in GLOBAL:
        if cid in GLOBAL.add_channel:
            if GLOBAL.add_channel[cid].add_channel is True:
                # Verify the forwarded message

                kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                cancel = telebot.types.InlineKeyboardButton("❌ Cancel",
                                                            callback_data='admin_channel=cancel')
                if m.forward_from_chat is None:
                    # Error!
                    kb.add(cancel)
                    if m.forward_from is None:
                        last_msg = bot.send_message(cid, "Error: You need to forward a message!\n\nPlease, try again.",
                                                    reply_markup=kb).wait()
                    else:
                        last_msg = bot.send_message(cid, "Error: The message must be from a channel!\n\n"
                                                         "Please, try again.",
                                                    reply_markup=kb).wait()

                    bot.delete_message(cid, GLOBAL.add_channel[cid].last_msg)
                    GLOBAL.add_channel[cid].last_msg = last_msg.message_id

                    return

                if m.forward_from_chat.type != 'channel':
                    # Error: Must be from a channel
                    kb.add(cancel)
                    last_msg = bot.send_message(cid, "Error: The message must be from a channel!\n\nPlease, try again.",
                                                reply_markup=kb).wait()
                    bot.delete_message(cid, GLOBAL.add_channel[cid].last_msg)
                    GLOBAL.add_channel[cid].last_msg = last_msg.message_id
                    return

                try:
                    fetching_info = bot.send_message(cid, "🕐 Fetching channel info...").wait()
                    channel = channels.get({'channel_id': m.forward_from_chat.id})
                    if channel is not None:
                        kb.add(cancel)
                        txt = "Error: The channel is already in the Network!\n\n" \
                              "Please, try again with other channel."
                        last_msg = bot.edit_message_text(chat_id=cid, text=txt, message_id=fetching_info.message_id,
                                                         reply_markup=kb).wait()
                        bot.delete_message(cid, GLOBAL.add_channel[cid].last_msg)
                        GLOBAL.add_channel[cid].last_msg = last_msg.message_id
                        return
                    bot.delete_message(cid, GLOBAL.add_channel[cid].last_msg)
                    loading_admins = bot.edit_message_text(chat_id=cid,
                                                           text="🕐 Done. Loading admins and Authenticating...",
                                                           message_id=fetching_info.message_id, reply_markup=kb).wait()
                    admins = bot.get_chat_administrators(m.forward_from_chat.id).wait()
                    if not isinstance(admins, list):
                        raise telebot.apihelper.ApiException('.', '.', '.')
                    user_is_creator = False
                    creator = None
                    for user in admins:
                        if user.status == 'creator':
                            creator = user.user
                            if user.user.id == cid:
                                user_is_creator = True

                                break

                    channel = bot.get_chat(m.forward_from_chat.id).wait()

                    if user_is_creator or cid in config.BOT_SUDO:
                        rendering = bot.edit_message_text(chat_id=cid, text="🕐 Done. Rendering Channel info...",
                                                          message_id=loading_admins.message_id, reply_markup=kb).wait()
                        if channel.photo is not None:
                            dl = bot.get_file(channel.photo.big_file_id).wait()
                            pic = bot.download_file(dl.file_path).wait()
                            if isinstance(pic, tuple):
                                raise Exception("{0} {1} {2}".format(pic[0], pic[1], 'add_channel', '.'))
                            with open('temp/'+str(dl.file_path), 'wb') as pro_pic:
                                pro_pic.write(pic)

                            with open('temp/'+str(dl.file_path), 'rb') as pro_pic:
                                p = bot.send_photo(config.PHOTOS_CHANNEL, pro_pic).wait()
                                photo_id = p.photo[len(p.photo) - 1].file_id

                            os.remove('temp/' + str(dl.file_path))
                        else:
                            photo_id = None
                        GLOBAL.add_channel[cid].channel_info.channel_name = channel.title
                        GLOBAL.add_channel[cid].channel_info.channel_info = channel.description
                        GLOBAL.add_channel[cid].channel_info.channel_username = channel.username
                        GLOBAL.add_channel[cid].channel_info.channel_private_link = channel.invite_link
                        GLOBAL.add_channel[cid].channel_info.channel_profile_pic = photo_id
                        GLOBAL.add_channel[cid].channel_info.channel_creator.name = creator.first_name
                        GLOBAL.add_channel[cid].channel_info.channel_creator.username = creator.username
                        GLOBAL.add_channel[cid].channel_info.channel_creator.id = creator.id
                        GLOBAL.add_channel[cid].channel_info.channel_id = m.forward_from_chat.id

                        txt = 'All right. Here\'s your channel info:\n\n' \
                              '🖼 *Channel Profile Pic.*\n {0}\n\n' \
                              '🖋 *Channel Name*\n {1}\n\n' \
                              '🔖 *Channel Username* \n{2}\n\n' \
                              '🔐 *Channel Private Link*\n {3}\n\n' \
                              '💬 *Channel Description* \n`{4}`\n\n' \
                              '_Additional info may be requested before adding this channel to the network._'.format(
                                '/view\_\_' + photo_id.replace('_', '\_') if photo_id is not None
                                else 'None',
                                channel.title.replace('_', '\_').replace('*', '\*').replace('`', '\`'),
                                '@' + channel.username.replace('_', '\_') if channel.username is not None else 'None',
                                '[|Link|](' + channel.invite_link + ')' if channel.invite_link is not None else 'None',
                                channel.description
                              )

                        send_btn = telebot.types.InlineKeyboardButton("🚀 Send for Approval",
                                                                      callback_data='admin_channel=add_channel '
                                                                                    'to_approve=%s' % cid)
                        kb.add(send_btn)
                        kb.add(cancel)
                        return bot.edit_message_text(chat_id=cid, text=txt, message_id=rendering.message_id,
                                                     reply_markup=kb, parse_mode='markdown').wait()

                    else:
                        del GLOBAL.add_channel[cid]
                        from components.callback_kbbuttons import main_menu_admin
                        kb = main_menu_admin(cid)
                        bot.edit_message_text(chat_id=cid,
                                              text="Authentication failed: You're not this channel's creator.\n\n"
                                                   "Sorry, but only the chat creator can add a channel.",
                                              message_id=loading_admins.message_id, reply_markup=kb).wait()
                        return bot.send_message(chat_id=cid, text="Sorry, but only the chat creator can add a channel.",
                                                reply_markup=kb)

                except telebot.apihelper.ApiException:
                    kb.add(cancel)
                    last_msg = bot.send_message(cid,
                                                "I am not admin at your channel!.\n\n"
                                                "Please, add me as admin, and try again.", reply_markup=kb).wait()
                    bot.delete_message(cid, GLOBAL.add_channel[cid].last_msg)
                    GLOBAL.add_channel[cid].last_msg = last_msg.message_id
                    return

                except Exception as e:
                    import traceback
                    utils.report_msg(bot, m, GLOBAL, e, str(traceback.format_exc()))
                    logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))

    reload(components)
    return components.posts.posts_handler(bot, m, GLOBAL, files_main)


select_channels = ['next_channels', 'previous_channels']


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] in select_channels)
def sel_channels(call):
    if call.message:
        cid = call.from_user.id
        try:
            split_data = call.data.split()
            func = split_data[0].split('=')[0]
            arg = split_data[0].split('=')[1]

            if func == 'next_channels' or func == 'previous_channels':
                n = int(arg)
                kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                btns = []
                if cid in config.BOT_SUDO:
                    auth_channels = config.ch_list
                    b_channels = auth_channels[(6*n):]
                else:

                    member = members.get({'user_id': cid})
                    auth_channels = member['owned_channels'] + member['authorized_channels']
                    a_channels = auth_channels[(6 * n):]
                    b_channels = []
                    for i in a_channels:
                        ch = channels.get({'channel_id': i})
                        b_channels.append(ch)
                if len(b_channels) > 6:
                    ct = 6
                else:
                    ct = len(b_channels)

                for i in range(ct):
                    btn = telebot.types.InlineKeyboardButton(b_channels[i]['channel_name'],
                                                             callback_data="new_post=%s" % b_channels[i][
                                                                     'channel_id'])
                    btns.append(btn)

                next_button = telebot.types.InlineKeyboardButton("▶️", callback_data="next_channels=%s" % (n + 1))
                previous_button = telebot.types.InlineKeyboardButton("◀️",
                                                                     callback_data="previous_channels=%s" % (n - 1))

                kb.add(*btns)
                if len(auth_channels) <= 6 * (n + 1):
                    kb.add(previous_button)

                elif len(auth_channels) > (6 * (n + 1)) and n - 1 >= 0:
                    kb.add(previous_button, next_button)

                else:
                    kb.add(next_button)

                bot.edit_message_reply_markup(cid, call.message.message_id, call.id, reply_markup=kb)
        except Exception as e:
            import traceback
            utils.report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data: " + call.data)
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


@bot.callback_query_handler(func=lambda call: call.data.split()[0].split('=')[0] == 'new_post')
def new_post_channel(call):
    if call.message:
        cid = call.from_user.id
        try:
            split_data = call.data.split()
            ch = int(split_data[0].split('=')[1])

            # channel = {"channel_id": -1001132758250, "channel_username": "Lol", "channel_name": "Test"}
            channel = channels.get({'channel_id': ch})
            default_caption = channel.get('channel_caption', None)
            reactions_default = channel.get('channel_reactions', None)

            main_tags = channel['channel_tags'] if 'channel_tags' in channel else []

            GLOBAL.create_post[cid] = utils.Dictionary(
                {
                    'queue': True,
                    'channel': ch,
                    'disable_web_page_preview': False,
                    'default_caption': default_caption,
                    'reactions': reactions_default,
                    'default_silenced': False,
                    'main_tags': main_tags,
                    'posts': utils.Dictionary()
                }
            )
            if ch in config.CHANNELS:
                GLOBAL.create_post[cid].zig_zag = False

            txt = "Creating posts for *{0}*.\n\n" \
                  "Tap the \"Options\" to change post's default reactions and " \
                  "web page preview.".format(channel['channel_name'])

            btns = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, one_time_keyboard=True)

            options_btn = telebot.types.KeyboardButton("📋 Options")
            clear = telebot.types.KeyboardButton("🗑 Clear All")
            preview_all = telebot.types.KeyboardButton("👁 Preview")
            send_all = telebot.types.KeyboardButton("🚀 Post")
            save_draft = telebot.types.KeyboardButton("✏ Save Draft")
            cancel_post = telebot.types.KeyboardButton("❌ Cancel")

            btns.add(send_all)
            btns.row(options_btn, preview_all)
            btns.row(clear, save_draft)
            btns.add(cancel_post)

            bot.send_message(cid, txt, reply_markup=btns, parse_mode='markdown')
            return bot.delete_message(cid, call.message.message_id)
        except Exception as e:
            import traceback
            utils.report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data: " + call.data)
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'delete_message':
        return bot.delete_message(call.message.chat.id, call.message.message_id)
    reload(components)
    return components.callbackquery.callback_handler(bot, call, GLOBAL)


def main_loop():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=50)
        except KeyboardInterrupt:
            print(sys.stderr, '\nExiting by user request.\n')
            reactions_cache.stop()
            deep_link_cache.stop()
            sys.exit(0)
        except Exception as e:
            raise e
            # time.sleep(2)
            # os.execv(sys.executable, ['python'] + sys.argv)


if __name__ == '__main__':
    try:
        # Remove webhook, it fails sometimes the set if there is a previous webhook
        bot.remove_webhook()
        main_loop()
        # Set webhook
        """bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                        certificate=open(WEBHOOK_SSL_CERT, 'r'))

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

        # Start aiohttp server
        web.run_app(
            app,
            host=WEBHOOK_LISTEN,
            port=WEBHOOK_PORT,
            ssl_context=context)"""
    except KeyboardInterrupt:
        print(sys.stderr, '\nExiting by user request.\n')
        reactions_cache.stop()
        deep_link_cache.stop()
        sys.exit(0)
    except Exception as e:
        reactions_cache.stop()
        deep_link_cache.stop()
        python = sys.executable
        os.execl(python, python, *sys.argv)
        raise e
