import telebot
import config
from utils import owner_access, Dictionary, report_msg, str_generator
from Main import logger, members, channels, deep_link_cache, files
from Strings import Channel
# import sys


@owner_access(log=logger, db=members)
def channel_management(bot, m):
    cid = m.chat.id
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    member = members.get({'user_id': cid})
    owned_channels = member['owned_channels']
    add_channel = telebot.types.InlineKeyboardButton("➕ Add a Channel", callback_data='admin_channel=add_channel')
    edit_channel = telebot.types.InlineKeyboardButton("✏️ Edit a Channel", callback_data='admin_channel=edit_channel')
    remove_channel = telebot.types.InlineKeyboardButton("🗑 Remove a Channel", callback_data='admin_channel=del_channel')
    if cid not in config.BOT_SUDO:
        if len(owned_channels) < 1:
            buttons.add(add_channel)
        else:
            buttons.row(add_channel, edit_channel)
            buttons.add(remove_channel)
    else:
        buttons.row(add_channel, edit_channel)
        buttons.add(remove_channel)
    return bot.send_message(cid, "Select an Option", reply_markup=buttons)


def call_channel_management(bot, call, gl, ch_list):
    if call.message:
        cid = call.message.chat.id
        try:
            splt_data = call.data.split()
            kb = telebot.types.InlineKeyboardMarkup(row_width=2)

            _call = splt_data[0].split('=')[1]

            if _call == 'add_channel':
                if len(splt_data) < 2:
                    txt = 'Please, add me to your channel, and forward a message from your channel.\n\n' \
                          '_Note: The message must be from your channel, not forwarded from elsewhere!_'
                    if 'add_channel' not in gl:
                        gl.add_channel = Dictionary({})

                    cancel = telebot.types.InlineKeyboardButton("❌ Cancel",
                                                                callback_data='admin_channel=cancel')
                    kb.add(cancel)

                    gl.add_channel[cid] = Dictionary({'add_channel': True,
                                                      'last_msg': call.message.message_id,
                                                      'channel_info': Dictionary({
                                                          'channel_name': None,
                                                          'channel_info': None,
                                                          'channel_username': None,
                                                          'channel_private_link': None,
                                                          'channel_profile_pic': None,
                                                          'channel_tier': None,
                                                          'channel_tags': [],
                                                          'channel_creator': Dictionary({'name': None,
                                                                                         'username': None,
                                                                                         'id': None
                                                                                         }
                                                                                        ),
                                                          'channel_id': None,

                                                        }
                                                       )
                                                      }
                                                     )
                    return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                 parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

                else:
                    func = splt_data[1].split('=')[0]
                    if func == 'to_approve':
                        uid = int(splt_data[1].split('=')[1])
                        if 'add_channel' not in gl or cid not in gl.add_channel:
                            txt = "Error: Channel info not cached / missing.\n\n" \
                                  "This error may be caused because the server restarted and lost the cached info " \
                                  "in-memory.\n\n" \
                                  "Please, try to add your channel again."
                            bot.answer_callback_query(callback_query_id=call.id, text=txt, show_alert=True)
                            call.data = 'admin_channel=back'
                            return call_channel_management(bot, call, gl, ch_list)

                        cinfo = gl.add_channel[uid].channel_info
                        txt = 'User {0} {1} requested to add the following channel:\n\n' \
                              '🖼 *Channel Profile Pic.*\n {2}\n\n' \
                              '🖋 *Channel Name*\n {3}\n\n' \
                              '🔖 *Channel Username*\n {4}\n\n' \
                              '🔐 *Channel Private Link*\n {5}\n\n' \
                              '💬 *Channel Description* \n`{6}`\n\n' \
                              ''.format(
                               call.from_user.first_name.replace('_', '\_').replace('*', '\*').replace('`', '\`'),
                               call.from_user.id,
                               '/view\_\_' + cinfo.channel_profile_pic.replace('_', '\_') if
                               cinfo.channel_profile_pic is not None else 'None',
                               cinfo.channel_name.replace('_', '\_').replace('*', '\*').replace('`', '\`'),
                               '@' + cinfo.channel_username.replace('_', '\_') if cinfo.channel_username is not None
                               else 'None',
                               '[|Link|](' + cinfo.channel_private_link + ')' if cinfo.channel_private_link is not None
                               else 'None',
                               cinfo.channel_info
                              )
                        if 'approve_channel' not in gl:
                            gl.approve_channel = Dictionary({})
                        code = str_generator(6)
                        gl.approve_channel[code] = gl.add_channel[uid]
                        del gl.add_channel[uid]
                        yes_btn = telebot.types.InlineKeyboardButton("Yes", callback_data='admin_channel=add_channel '
                                                                                          'channel_approved=Yes '
                                                                                          'code=%s' % code)
                        no_btn = telebot.types.InlineKeyboardButton("No", callback_data='admin_channel=add_channel '
                                                                                        'channel_approved=No '
                                                                                        'code=%s' % code)
                        kb.add(yes_btn, no_btn)
                        bot.send_message(chat_id=196309422, text=txt, reply_markup=kb, parse_mode='markdown')

                        bot.answer_callback_query(callback_query_id=call.id, text="Channel sent to approval.")
                        call.data = 'admin_channel=back'
                        return call_channel_management(bot, call, gl, ch_list)

                    elif func == 'channel_approved':
                        """'admin_channel=add_channel channel_approved=Yes code=%s'"""
                        reason = splt_data[1].split('=')[1]
                        code = splt_data[2].split('=')[1]
                        if 'approve_channel' not in gl or code not in gl.approve_channel:
                            txt = "Error: Channel info not cached / missing.\n\n" \
                                  "This error may be caused because the server restarted and lost the cached info " \
                                  "in-memory.\n\n" \
                                  "Please, try to add your channel again."
                            bot.answer_callback_query(callback_query_id=call.id, text=txt, show_alert=True)
                            call.data = 'admin_channel=back'
                            return call_channel_management(bot, call, gl, ch_list)
                        uid = gl.approve_channel[code].channel_info.channel_creator.id
                        if reason == 'Yes':
                            cinfo = gl.approve_channel[code].channel_info
                            channels.write(cinfo)
                            members.update({'user_id': cinfo.channel_creator.id},
                                           {'$addToSet': {'owned_channels': cinfo.channel_id}})
                            if cinfo.channel_creator.id in config.BOT_SUDO:
                                for i in config.BOT_SUDO:
                                    members.update({'user_id': i},
                                                   {'$addToSet': {'owned_channels': cinfo.channel_id}})
                            bot.send_message(uid, 'Your channel was added to our database!\n\n '
                                                  'We welcome {} to the Network!'.format(cinfo.channel_name))

                            del gl.approve_channel[code]
                            config.ch_list = channels.search({})
                            return bot.edit_message_text("Channel Added to the database.", cid, call.message.message_id,
                                                         call.id, disable_web_page_preview=True)

                        elif reason == 'No':
                            bot.send_message(uid, 'Aww, blood and guts. Your channel was rejected.')

                            del gl.add_channel[code]
                            return bot.edit_message_text("Channel Rejected.", cid, call.message.message_id,
                                                         call.id, disable_web_page_preview=True)
                        else:
                            pass

            elif _call == 'edit_channel':
                bts = []
                if cid in config.BOT_SUDO:
                    all_channels = channels.search({})

                    for channel in all_channels:
                        ch_name = channel['channel_name']
                        ch_id = channel['channel_id']
                        btn = telebot.types.InlineKeyboardButton(text=ch_name, callback_data='admin_channel=%d' % ch_id)
                        bts.append(btn)
                    if len(bts) < 1:
                        txt = "You don't have any registered channels!"
                    else:
                        txt = "Select in the list below the channel you wish to manage."
                    kb.add(*bts)
                    back = telebot.types.InlineKeyboardButton("🔙", callback_data='admin_channel=back')
                    kb.add(back)
                    return bot.edit_message_text(txt, cid,
                                                 call.message.message_id, call.id, parse_mode='markdown',
                                                 reply_markup=kb, disable_web_page_preview=True)

                owner = members.get({'user_id': int(cid)})

                owned_channels = owner['owned_channels']

                if len(owned_channels) < 1:
                    btn = telebot.types.InlineKeyboardButton("➕ Add a Channel", callback_data='new_channel=%d' % cid)
                    kb.add(btn)
                    return bot.edit_message_text("You do now own any channel! Start a new channel process by "
                                                 "pressing the button.", cid, call.message.message_id, call.id,
                                                 parse_mode='markdown', reply_markup=kb,
                                                 disable_web_page_preview=True)

                for i in owned_channels:
                    channel = channels.get({'channel_id': i})
                    ch_name = channel['channel_name']
                    btn = telebot.types.InlineKeyboardButton(text=ch_name, callback_data='admin_channel=%d' % i)
                    bts.append(btn)
                kb.add(*bts)

                back = telebot.types.InlineKeyboardButton("🔙", callback_data='admin_channel=back')
                kb.add(back)

                return bot.edit_message_text("Select in the list below the channel you wish to manage.", cid,
                                             call.message.message_id, call.id, parse_mode='markdown', reply_markup=kb,
                                             disable_web_page_preview=True)

            elif _call == 'del_channel':
                if len(splt_data) < 2:
                    txt = 'Choose a Channel you\'d like to remove.'

                    if cid in config.BOT_SUDO:
                        owned_channels = [i['channel_id'] for i in channels.search({})]

                    else:
                        member = members.get({'user_id': cid})
                        if member is None:
                            return

                        owned_channels = member['owned_channels']

                    if len(owned_channels) < 1:
                        txt = 'You do not have any channels registered!'

                    else:
                        lst = []
                        for channel in owned_channels:
                            channel = channels.get({'channel_id': int(channel)})

                            btn = telebot.types.InlineKeyboardButton("✖️ %s" % channel['channel_name'],
                                                                     callback_data='admin_channel=del_channel '
                                                                                   'del=%d '
                                                                                   'conf=0' % channel['channel_id'])
                            lst.append(btn)

                        kb.add(*lst)

                    back = telebot.types.InlineKeyboardButton("🔙", callback_data='admin_channel=back')
                    kb.add(back)

                    return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                 parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

                else:
                    del_channel = splt_data[1].split('=')[1]
                    conf = splt_data[2].split('=')[1]

                    if conf == 'Yes':

                        channels.delete({'channel_id': int(del_channel)})
                        members.update_many({}, {'$pullAll': {'owned_channels': [int(del_channel)]}})
                        members.update_many({}, {'$pullAll': {'authorized_channels': [int(del_channel)]}})
                        members.update_many({}, {'$pull': {'posts': {'channel': int(del_channel)}}})
                        files.delete_many({'channel': int(del_channel)})

                        bot.answer_callback_query(callback_query_id=call.id, text="Channel removed.")
                        call.data = 'admin_channel=del_channel'
                        ch_list = channels.search({})

                        return call_channel_management(bot, call, gl, ch_list)

                    elif conf == 'No':
                        call.data = 'admin_channel=del_channel'

                        return call_channel_management(bot, call, gl, ch_list)
                    else:
                        txt = 'Are you sure you want to remove this channel?\n' \
                              '_By removing a channel, you\'ll delete all previous posts made for this channel on the' \
                              ' database, reactions, saved analytics data and remove all admins.\n\n' \
                              'This action can not be undone._'

                        yes_btn = telebot.types.InlineKeyboardButton("Yes", callback_data='admin_channel=del_channel '
                                                                                          'del=%s '
                                                                                          'conf=Yes' % del_channel)
                        no_btn = telebot.types.InlineKeyboardButton("No", callback_data='admin_channel=del_channel '
                                                                                        'del=%s '
                                                                                        'conf=No' % del_channel)
                        kb.add(yes_btn, no_btn)

                        return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                     parse_mode='markdown', reply_markup=kb,
                                                     disable_web_page_preview=True)

            elif _call == 'back':

                member = members.get({'user_id': cid})
                owned_channels = member['owned_channels']
                add_channel = telebot.types.InlineKeyboardButton("➕ Add a Channel",
                                                                 callback_data='admin_channel=add_channel')
                edit_channel = telebot.types.InlineKeyboardButton("✏️ Edit a Channel",
                                                                  callback_data='admin_channel=edit_channel')
                remove_channel = telebot.types.InlineKeyboardButton("🗑 Remove a Channel",
                                                                    callback_data='admin_channel=del_channel')

                if cid not in config.BOT_SUDO:
                    if len(owned_channels) < 1:
                        kb.add(add_channel)
                    else:
                        kb.row(add_channel, edit_channel)
                        kb.add(remove_channel)
                else:
                    kb.row(add_channel, edit_channel)
                    kb.add(remove_channel)
                return bot.edit_message_text("Select an Option", cid, call.message.message_id, call.id,
                                             parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

            elif _call == 'cancel':
                bot.answer_callback_query(callback_query_id=call.id, text="Operation canceled.")

                call.data = 'admin_channel=back'
                if 'add_channel' in gl:
                    if cid in gl.add_channel:
                        del gl.add_channel[cid]

                return call_channel_management(bot, call, gl, ch_list)

            else:
                ch_id = int(splt_data[0].split('=')[1])
                channel = channels.get({'channel_id': ch_id})
                if channel is None:
                    return

                kb = telebot.types.InlineKeyboardMarkup(row_width=4)

                edit_tier = telebot.types.InlineKeyboardButton("Tier: %s" % channel.get('channel_tier', None),
                                                               callback_data='edit_channel=%d '
                                                                             'editing=tier tier=%s' %
                                                                             (ch_id,
                                                                              'SFW' if
                                                                              channel.get('channel_tier', None) is
                                                                              None else 'NSFW' if
                                                                              channel.get('channel_tier', None) == 'SFW'
                                                                              else 'OTHER' if
                                                                              channel.get('channel_tier', None) ==
                                                                              'NSFW'
                                                                              else 'None'
                                                                              if channel.get('channel_tier', None) ==
                                                                                 'OTHER' else 'None')) if \
                    cid in config.BOT_SUDO else None

                edit_main_tags = telebot.types.InlineKeyboardButton("#️⃣ Edit Tags",
                                                                    callback_data='edit_channel=%d '
                                                                                  'editing=tags' % ch_id)

                edit_name = telebot.types.InlineKeyboardButton("🖋 Edit Name",
                                                               callback_data='edit_channel=%d editing=name' % ch_id)
                edit_info = telebot.types.InlineKeyboardButton("💬 Edit Description",
                                                               callback_data='edit_channel=%d '
                                                                             'editing=description' % ch_id)
                edit_username = telebot.types.InlineKeyboardButton("🔖 Edit Alias",
                                                                   callback_data='edit_channel=%d '
                                                                                 'editing=username' % ch_id)
                edit_link = telebot.types.InlineKeyboardButton("🔐 Edit Private Link",
                                                               callback_data='edit_channel=%d editing=link' % ch_id)

                edit_profile_pic = telebot.types.InlineKeyboardButton("🖼 Edit Profile Pic.",
                                                                      callback_data='edit_channel=%d '
                                                                                    'editing=profile_pic' % ch_id)
                edit_admins = telebot.types.InlineKeyboardButton("👮 Edit Admins",
                                                                 callback_data='edit_channel=%d editing=admins' % ch_id)

                post_preferences = telebot.types.InlineKeyboardButton("🚀 Post Preferences",
                                                                      callback_data='edit_channel=%d '
                                                                                    'post_preferences=True' % ch_id)
                save = telebot.types.InlineKeyboardButton("✅ Save and Exit",
                                                          callback_data='edit_channel=%d save=True' % ch_id)

                if cid in config.BOT_SUDO:
                    kb.row(edit_tier, edit_main_tags)
                else:
                    kb.add(edit_main_tags)
                kb.row(edit_profile_pic, edit_name)
                kb.row(edit_username, edit_link)
                kb.row(edit_info, edit_admins)
                kb.add(post_preferences)
                kb.add(save)

                text = 'Let\'s edit this channel\'s info.\nHere\'s what I have:\n\n' \
                       '🖼 *Channel Profile Pic.:*\n {0}\n\n' \
                       '🖋 *Channel Name*\n {1}\n\n' \
                       '🔖 *Channel Username*\n {2}\n\n' \
                       '🔐 *Channel Private Link*\n {3}\n\n' \
                       '👮 *Authorized Admins*\n {4}\n\n' \
                       '💬 *Channel Description* \n`{5}`\n\n' \
                       '#️⃣ *Channel Tags*\n{6}\n\n' \
                       '😂 *Default Reactions*\n{7}\n\n' \
                       '📋 *Default Captions*\n{8}\n\n' \

                auth_admins = members.search({'authorized_channels': ch_id})
                if len(auth_admins) < 1:
                    auth_admins = '_You have no authorized admins!_'
                else:
                    auth_admins = ', '.join(['_%s_' % i['user_name'] for i in auth_admins])

                channel = channels.get({'channel_id': ch_id})
                channel_profile_pic = channel['channel_profile_pic']
                channel_name = channel['channel_name']
                channel_description = channel['channel_info']
                channel_alias = channel['channel_username']
                channel_private_link = channel['channel_private_link']
                channel_tags = ' '.join(channel['channel_tags']).replace('_', '\_') if \
                    len(channel['channel_tags']) > 0 else "_Your channel have no main tags!_"
                default_reactions = channel.get('channel_reactions', None) if \
                    channel.get('channel_reactions', None) is not None else \
                    '_Your channel have no default Reactions!_'
                default_captions = channel.get('channel_caption', None).replace("_", "\_").replace("*", "\*")\
                    .replace("`", "\`") if \
                    channel.get('channel_caption', None) is not None else '_Your channel have no default Captions!_'

                text = text.format('/view\_\_' + channel_profile_pic.replace('_', '\_') if channel_profile_pic is not
                                   None else 'None',
                                   channel_name.replace('_', '\_').replace('*', '\*').replace('`', '\`') if
                                   channel_name is not None else 'None',
                                   '@' + channel_alias.replace('_', '\_').replace('*', '\*').replace('`', '\`') if
                                   channel_alias is not None else 'None',
                                   '[|Link|](' + channel_private_link + ')' if channel_private_link is not None
                                   else 'None', auth_admins, channel_description, channel_tags, default_reactions,
                                   default_captions)

                text += '\n\nOwner: %s' % channel['channel_creator']['name'] if cid in config.BOT_SUDO else ''
                if 'edit_channel_info' not in gl:
                    gl.edit_channel_info = Dictionary()
                gl.edit_channel_info[cid] = Dictionary(
                    {
                        'channel_id': ch_id,
                        'edit_channel': True,
                        'channel_info': Dictionary(
                            {
                                'channel_name': channel_name,
                                'channel_info': channel_description,
                                'channel_username': channel_alias,
                                'channel_private_link': channel_private_link,
                                'channel_profile_pic': channel_profile_pic,
                                'channel_tags': channel['channel_tags'],
                                'channel_tier': channel.get('channel_tier', None),
                                'default_reactions': channel.get('channel_reactions', None),
                                'default_captions': channel.get('channel_caption', None),
                                'channel_creator': channel['channel_creator']
                            })
                    }
                )
                kb1 = telebot.types.ReplyKeyboardRemove(selective=False)
                dell = bot.send_message(cid, '🕐 Loading Context...', reply_markup=kb1)
                bot.delete_message(cid, dell.wait().message_id)
                return bot.edit_message_text(text, cid, call.message.message_id, call.id,
                                             parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

        except Exception as e:
            import traceback
            from Main import GLOBAL
            report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data:" + call.data)
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


def edit_channel_management(bot, call, gl):
    if call.message:
        cid = call.message.chat.id
        try:
            splt = call.data.split()
            editing_channel = int(splt[0].split('=')[1])
            func = splt[1].split('=')[0]
            param = splt[1].split('=')[1]
            kb = telebot.types.InlineKeyboardMarkup(row_width=2)
            back = telebot.types.InlineKeyboardButton("🔙", callback_data='edit_channel=%d back=True' % editing_channel)

            if 'edit_channel_info' not in gl or cid not in gl.edit_channel_info:
                txt = "Error: Channel info not cached / missing.\n\n" \
                      "This error may be caused because the server restarted and lost the cached info in-memory.\n\n" \
                      "Please, try to add your channel again."
                bot.answer_callback_query(call.id, txt, show_alert=True)
                call.data = 'admin_channel=edit_channel'
                return call_channel_management(bot, call, gl, None)
            if func == 'add_admins':
                # This part is to know if the call stack for adding admins was previously made.
                # Here, we get the whole deep link cache.
                cache_view = deep_link_cache.view()

                # Here, we get all deep link calls that have the 'add_admin' call
                ly = {cache_view[i]['data']['channel']: i
                      for i in cache_view if 'call' in cache_view[i]['data'] and
                      cache_view[i]['data']['call'] == 'add_admin'}

                # Finally, generates the code if the editing channel has not been previously cached to add admin; uses
                # The previous code otherwise.
                code = ly[editing_channel] if editing_channel in ly else str_generator(8)
                channel = channels.get({'channel_id': editing_channel})
                label = '**Admin for %s!**' % channel['channel_name'].replace("(", "").replace(")", "")
                ttxt = '\n' \
                       'Become now admin at this channel by clicking on this following link:\n' \
                       't.me/LilianRobot?start=%s' % code
                l_txt = 'https://t.me/share/url?url={label}&text={txt}'.format(
                    label=label.replace(" ", "%20"),
                    txt=ttxt.replace(" ", "%20").replace("/", "%2F").replace(":", "%3A").replace("?", "%3F").
                        replace("=", "%3D").replace('\n', '%0A'))
                txt = '[Click Here and share](%s) your channel for your future admins.\n\n' \
                      'Remember, this link will automatically expire in one hour, and will no longer be available' \
                      ' to add new admins.' % l_txt
                if editing_channel not in ly:
                    deep_link_cache.add(code, {'call': 'add_admin', 'channel': editing_channel}, 60*60)

                kb.add(back)

            elif func == 'del_admins':
                if param == 'True':
                    txt = 'Select the Admin you\'d like to remove.'

                    auth_admins = members.search({'authorized_channels': int(editing_channel)})
                    if auth_admins is None or auth_admins == []:
                        txt = 'You have no admins for your channel.'
                    else:
                        bt_list = []

                        for admin in auth_admins:
                            btn = telebot.types.InlineKeyboardButton("✖ %s" % admin['user_name'],
                                                                     callback_data='edit_channel=%d '
                                                                                   'del_admins=%s' % (editing_channel,
                                                                                                      admin['user_id']))
                            bt_list.append(btn)

                        kb.add(*bt_list)
                    kb.add(back)

                elif param == 'Yes':
                    admin = splt[2].split('=')[1]
                    members.update({'user_id': int(admin)},
                                   {'$pullAll': {'authorized_channels': [int(editing_channel)]}})

                    bot.answer_callback_query(callback_query_id=call.id, text="Admin removed.")

                    call.data = 'edit_channel=%d del_admins=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                else:
                    member = members.get({'user_id': int(param)})
                    txt = 'Are you sure you want to remove *%s* as admin?' % member['user_name']

                    yes = telebot.types.InlineKeyboardButton("Yes",
                                                             callback_data='edit_channel=%d '
                                                                           'del_admins=Yes '
                                                                           'admin=%d' % (editing_channel,
                                                                                         member['user_id']))

                    no = telebot.types.InlineKeyboardButton("No",
                                                            callback_data='edit_channel=%d '
                                                                          'del_admins=True' % editing_channel)
                    kb.row(yes, no)

                return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                             parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

            elif func == 'back':
                tier = gl.edit_channel_info[cid].channel_info.channel_tier
                if tier == 'SFW':
                    next_tier = 'NSFW'
                elif tier == 'NSFW':
                    next_tier = 'OTHER'
                elif tier == 'OTHER':
                    next_tier = 'None'
                else:
                    next_tier = 'SFW'
                edit_tier = telebot.types.InlineKeyboardButton("Tier: %s" % tier,
                                                               callback_data='edit_channel=%d '
                                                                             'editing=tier tier=%s' %
                                                                             (editing_channel,
                                                                              next_tier)
                                                               ) if cid in config.BOT_SUDO else None

                edit_main_tags = telebot.types.InlineKeyboardButton("#️⃣ Edit Tags",
                                                                    callback_data='edit_channel=%d '
                                                                                  'editing=tags' % editing_channel)

                edit_name = telebot.types.InlineKeyboardButton("🖋 Edit Name",
                                                               callback_data='edit_channel=%d '
                                                                             'editing=name' % editing_channel)
                edit_info = telebot.types.InlineKeyboardButton("💬 Edit Description",
                                                               callback_data='edit_channel=%d '
                                                                             'editing=description' % editing_channel)
                edit_username = telebot.types.InlineKeyboardButton("🔖 Edit Alias",
                                                                   callback_data='edit_channel=%d '
                                                                                 'editing=username' % editing_channel)
                edit_link = telebot.types.InlineKeyboardButton("🔐 Edit Private Link",
                                                               callback_data='edit_channel=%d '
                                                                             'editing=link' % editing_channel)

                edit_profile_pic = telebot.types.InlineKeyboardButton("🖼 Edit Profile Pic.",
                                                                      callback_data='edit_channel=%d '
                                                                                    'editing=profile_pic' %
                                                                                    editing_channel)
                edit_admins = telebot.types.InlineKeyboardButton("👮 Edit Admins",
                                                                 callback_data='edit_channel=%d '
                                                                               'editing=admins' % editing_channel)
                post_preferences = telebot.types.InlineKeyboardButton("🚀 Post Preferences",
                                                                      callback_data='edit_channel=%d '
                                                                                    'post_preferences=True' %
                                                                                    editing_channel)
                save = telebot.types.InlineKeyboardButton("✅ Save and Exit",
                                                          callback_data='edit_channel=%d save=True' % editing_channel)

                if cid in config.BOT_SUDO:
                    kb.row(edit_tier, edit_main_tags)
                else:
                    kb.add(edit_main_tags)
                kb.row(edit_profile_pic, edit_name)
                kb.row(edit_username, edit_link)
                kb.row(edit_info, edit_admins)
                kb.add(post_preferences)
                kb.add(save)

                text = 'Let\'s keep editing this channel\'s info.\nHere\'s what I have:\n\n' \
                       '🖼 *Channel Profile Pic.*\n {0}\n\n' \
                       '🖋 *Channel Name*\n {1}\n\n' \
                       '🔖 *Channel Username*\n {2}\n\n' \
                       '🔐 *Channel Private Link*\n {3}\n\n' \
                       '👮 *Authorized Admins*\n {4}\n\n' \
                       '💬 *Channel Description* \n`{5}`\n\n' \
                       '#️⃣ *Channel Tags*\n{6}\n\n' \
                       '😂 *Default Reactions*\n{7}\n\n' \
                       '📋 *Default Captions*\n{8}\n\n' \
                       '_For this changes to be made, you must save_'

                channel = gl.edit_channel_info[cid].channel_info

                channel_admins = members.search({'authorized_channels': editing_channel})
                if len(channel_admins) < 1:
                    channel_admins = '_You have no authorized admins!_'
                else:
                    channel_admins = ', '.join(['_%s_' % i['user_name'] for i in channel_admins])

                channel_profile_pic = channel['channel_profile_pic']
                channel_name = channel['channel_name']
                channel_description = channel['channel_info']
                channel_alias = channel['channel_username']
                channel_private_link = channel['channel_private_link']
                channel_tags = ' '.join(channel['channel_tags']).replace('_', '\_') if \
                    len(channel['channel_tags']) > 0 else "_Your channel have no main tags!_"
                default_reactions = channel.get('default_reactions', None) if \
                    channel.get('default_reactions', None) is not None else '_Your channel have no default Reactions!_'
                default_captions = channel.get('default_captions', None).replace("_", "\_")\
                    .replace("*", "\*").replace("`", "\`") if \
                    channel.get('default_captions', None) is not None else '_Your channel have no default Captions!_'

                txt = text.format('/view\_\_' + channel_profile_pic.replace('_', '\_') if channel_profile_pic is not
                                  None else 'None',
                                  channel_name.replace('_', '\_').replace('*', '\*').replace('`', '\`') if
                                  channel_name is not None else 'None',
                                  '@' + channel_alias.replace('_', '\_').replace('*', '\*').replace('`', '\`') if
                                  channel_alias is not None else 'None',
                                  '[|Link|](' + channel_private_link + ')' if channel_private_link
                                  is not None else 'None',
                                  channel_admins, channel_description, channel_tags, default_reactions, default_captions
                                  )
                txt += '\n\nOwner: %s' % channel['channel_creator']['name'] if cid in config.BOT_SUDO else ''

            elif func == 'save':
                bot.edit_message_text("🕐 Saving changes...", cid, call.message.message_id, call.id)
                try:
                    channel = gl.edit_channel_info[cid].channel_info
                    channels.update(
                        {
                            'channel_id': editing_channel
                        },
                        {
                            '$set':
                                {
                                    'channel_name': channel['channel_name'],
                                    'channel_info': channel['channel_info'],
                                    'channel_username': channel['channel_username'],
                                    'channel_profile_pic': channel['channel_profile_pic'],
                                    'channel_private_link': channel['channel_private_link'],
                                    'channel_tier': channel['channel_tier'],
                                    'channel_tags': channel['channel_tags'],
                                    'channel_caption': channel['default_captions'],
                                    'channel_reactions': channel['default_reactions']
                                }
                        }
                    )
                    from components import callback_kbbuttons
                    bts = callback_kbbuttons.main_menu_admin(cid)
                    bot.send_message(cid, "Done! All changes saved.", reply_markup=bts)
                    bot.delete_message(cid, call.message.message_id)
                    # ################### Updating the channel in the publisher #######################

                    s = channels.get({'channel_id': editing_channel})
                    if 'pub_id' in s:
                        try:
                            capt = '📢  %(hch)s%(ch_name)s \n\n🏷  %(desc)s' % {
                                'hch': '👁‍🗨' if s['channel_id'] in config.CHANNELS else '',
                                'ch_name': s['channel_name'],
                                'desc': s['channel_info'][:(198 - len(channel['channel_name']))] if
                                s['channel_info'] is not None else ''}
                            rating = '(+18)' if '#explicit' in s['channel_tags'] else '(+16)' if \
                                '#questionable' in s['channel_tags'] else ''

                            join_btn = telebot.types.InlineKeyboardButton('Join Now! ' + rating,
                                                                          url=s['channel_private_link'] if
                                                                          s[
                                                                              'channel_private_link'] is not None else
                                                                          't.me/' + s['channel_username'])
                            header = '**Join Now!**'.replace(" ", "%20")
                            text = '\nJoin now __{0}__, an amazing channel!\n\n' \
                                   't.me/HalksPUB/{1}'.format(s['channel_name'], s['pub_id']).replace(
                                    "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                                    "\n", "%0A").replace(",", "%2C").replace("=", "%3D").replace("+", "%2B")
                            url = 'https://t.me/share/url?url={0}&text={1}'.format(header, text)
                            share_btn = telebot.types.InlineKeyboardButton("Share with Friends!", url=url)
                            ke = telebot.types.InlineKeyboardMarkup(row_width=2)
                            ke.add(share_btn)
                            ke.add(join_btn)
                            bot.edit_message_caption(caption=capt, chat_id=config.PUB_CHANNEL, message_id=s['pub_id'],
                                                     reply_markup=ke)
                            bot.edit_message_reply_markup(chat_id=config.PUB_CHANNEL,
                                                          message_id=s['pub_id'], reply_markup=ke)

                        except Exception as e:
                            import traceback
                            report_msg(bot, call.message, gl, e, str(traceback.format_exc()), call.message.message_id)
                            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
                            print("ERROR IN UPDATING CHANNEL INFO ON @HALKSPUB")
                            pass

                    if 'edit_channel_info' in gl:
                        if cid in gl.edit_channel_info:
                            del gl.edit_channel_info[cid]
                except Exception as e:
                    import traceback
                    report_msg(bot, call.message, gl, e, str(traceback.format_exc()), call.message.message_id)
                    logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
                    pass

                bts = []
                if cid in config.BOT_SUDO:
                    all_channels = channels.search({})

                    for channel in all_channels:
                        ch_name = channel['channel_name']
                        ch_id = channel['channel_id']
                        btn = telebot.types.InlineKeyboardButton(text=ch_name, callback_data='admin_channel=%d' % ch_id)
                        bts.append(btn)

                    kb.add(*bts)
                    back = telebot.types.InlineKeyboardButton("🔙", callback_data='admin_channel=back')
                    kb.add(back)
                    return bot.send_message(cid, "Select in the list below the channel you wish to manage.",
                                            parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

                owner = members.get({'user_id': int(cid)})

                owned_channels = owner['owned_channels']

                if len(owned_channels) < 1:
                    btn = telebot.types.InlineKeyboardButton("➕ Add a Channel", callback_data='new_channel=%d' % cid)
                    kb.add(btn)
                    return bot.edit_message_text("You do now own any channel! "
                                                 "Tap the button below if you wish to add a channel.", cid,
                                                 call.message.message_id, call.id, parse_mode='markdown',
                                                 reply_markup=kb, disable_web_page_preview=True)

                for i in owned_channels:
                    channel = channels.get({'channel_id': i})
                    ch_name = channel['channel_name']
                    btn = telebot.types.InlineKeyboardButton(text=ch_name, callback_data='admin_channel=%d' % i)
                    bts.append(btn)
                kb.add(*bts)
                back = telebot.types.InlineKeyboardButton("🔙", callback_data='admin_channel=back')
                kb.add(back)

                return bot.edit_message_text("Select in the list below the channel you wish to manage.", cid,
                                             call.message.message_id, call.id, parse_mode='markdown', reply_markup=kb,
                                             disable_web_page_preview=True)

            elif func == 'cancel':
                if 'edit_channel_info' in gl:
                    if cid in gl.edit_channel_info:
                        del gl.edit_channel_info[cid].last_msg
                        gl.edit_channel_info[cid].edit_channel = True

                bot.answer_callback_query(callback_query_id=call.id, text="Operation Canceled.")

                call.data = 'edit_channel=%d back=True' % editing_channel
                return edit_channel_management(bot, call, gl)

            elif func == 'default_caption':
                if param == 'confirm':
                    gl.edit_channel_info[cid].channel_info.default_captions = gl.edit_channel_info[cid]\
                        .temp_default_caption
                    del gl.edit_channel_info[cid].temp_default_caption

                    bot.answer_callback_query(call.id, text="Done! You set the Default Captions.")
                    gl.edit_channel_info[cid].edit_channel = True
                    call.data = 'edit_channel=%d post_preferences=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                elif param == 'set':
                    gl.edit_channel_info[cid].edit_channel = 'set_default_caption'
                    gl.edit_channel_info[cid].last_msg = call.message.message_id
                    txt = 'Please, send the new default caption.\n\n' \
                          '💡 _Reminder: default captions will use a part of your caption, and they can not be ' \
                          'manually removed, unless the default caption is unset._'
                    kb = telebot.types.InlineKeyboardMarkup()
                    kb.add(
                        telebot.types.InlineKeyboardButton("❌ Cancel",
                                                           callback_data='edit_channel=%d '
                                                                         'default_caption=cancel' % editing_channel)
                    )

                elif param == 'delete':
                    gl.edit_channel_info[cid].channel_info.default_captions = None
                    bot.answer_callback_query(call.id, text="Done! Default Captions removed.")
                    call.data = 'edit_channel=%d post_preferences=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                elif param == 'cancel':
                    gl.edit_channel_info[cid].edit_channel = True
                    bot.answer_callback_query(call.id, 'You canceled. Default Captions not changed..')
                    call.data = 'edit_channel=%d post_preferences=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                else:
                    txt = 'What would you like to do with your default captions?'
                    kb = telebot.types.InlineKeyboardMarkup()
                    edit_capt = telebot.types.InlineKeyboardButton("📝 Edit",
                                                                   callback_data='edit_channel=%d '
                                                                                 'default_caption=set' % editing_channel
                                                                   )
                    del_capt = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                  callback_data='edit_channel=%d '
                                                                                'default_caption=delete' %
                                                                                editing_channel)
                    back = telebot.types.InlineKeyboardButton("🔙",
                                                              callback_data='edit_channel=%d '
                                                                            'post_preferences=True' % editing_channel)
                    kb.row(edit_capt, del_capt)
                    kb.add(back)

            elif func == 'default_reactions':

                if param == 'confirm':
                    gl.edit_channel_info[cid].channel_info.default_reactions = gl.edit_channel_info[cid].temp_reactions
                    del gl.edit_channel_info[cid].temp_reactions

                    bot.answer_callback_query(call.id, text="Done! You set the Default Reactions.")
                    gl.edit_channel_info[cid].edit_channel = True
                    call.data = 'edit_channel=%d post_preferences=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                elif param == 'set':
                    gl.edit_channel_info[cid].edit_channel = 'set_default_reaction'
                    gl.edit_channel_info[cid].last_msg = call.message.message_id
                    txt = 'Send me up to 4 emojis for the reactions without spacing or any kind of separation, ' \
                          'like the format below:\n\n' \
                          '👌😊😔😡\n\n' \
                          '💡 _Reminder: default reactions can be replaced by other reactions, although not ' \
                          'recommended, since it may break your pattern._'
                    kb = telebot.types.InlineKeyboardMarkup()
                    kb.add(
                        telebot.types.InlineKeyboardButton("❌ Cancel",
                                                           callback_data='edit_channel=%d '
                                                                         'default_reactions=cancel' % editing_channel)
                    )

                elif param == 'delete':
                    gl.edit_channel_info[cid].channel_info.default_captions = None
                    bot.answer_callback_query(call.id, text="Done! Default Reactions removed.")
                    call.data = 'edit_channel=%d post_preferences=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                elif param == 'cancel':
                    gl.edit_channel_info[cid].edit_channel = True
                    bot.answer_callback_query(call.id, 'You canceled. Default Reactions not changed..')
                    call.data = 'edit_channel=%d post_preferences=True' % editing_channel
                    return edit_channel_management(bot, call, gl)

                else:
                    txt = 'What would you like to do with your default captions?'
                    kb = telebot.types.InlineKeyboardMarkup()
                    edit_capt = telebot.types.InlineKeyboardButton("📝 Edit",
                                                                   callback_data='edit_channel=%d '
                                                                                 'default_reactions=set' %
                                                                                 editing_channel
                                                                   )
                    del_capt = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                  callback_data='edit_channel=%d '
                                                                                'default_reactions=delete' %
                                                                                editing_channel)
                    back = telebot.types.InlineKeyboardButton("🔙",
                                                              callback_data='edit_channel=%d '
                                                                            'post_preferences=True' % editing_channel)
                    kb.row(edit_capt, del_capt)
                    kb.add(back)

            elif func == 'post_preferences':
                txt = 'What would you like to do?'
                channel = gl.edit_channel_info[cid].channel_info

                if channel.default_captions is None:
                    default_caption_txt = "✏ Set a Default Caption"
                    default_caption_data = 'edit_channel=%d default_caption=set' % editing_channel
                else:
                    default_caption_txt = "📝 Edit the Default Caption"
                    default_caption_data = 'edit_channel=%d default_caption=edit' % editing_channel

                if channel.default_reactions is None:
                    default_reaction_text = '😂 Set Default Reactions'
                    default_reaction_data = 'edit_channel=%d default_reactions=set' % editing_channel
                else:
                    default_reaction_text = '👌 Edit the Default Reactions'
                    default_reaction_data = 'edit_channel=%d default_reactions=edit' % editing_channel

                df_re = telebot.types.InlineKeyboardButton(default_reaction_text, callback_data=default_reaction_data)
                df_ca = telebot.types.InlineKeyboardButton(default_caption_txt, callback_data=default_caption_data)
                kb.add(df_re)
                kb.add(df_ca)
                kb.add(back)

            else:
                if param == 'admins':
                    txt = 'What would you like to do?'
                    btn1 = telebot.types.InlineKeyboardButton("➕ Add Admins",
                                                              callback_data='edit_channel=%d '
                                                                            'add_admins=True' % editing_channel)
                    btn2 = telebot.types.InlineKeyboardButton("❌ Remove Admins",
                                                              callback_data='edit_channel=%d '
                                                                            'del_admins=True' % editing_channel)
                    auth_admins = members.search({'authorized_channels': int(editing_channel)})
                    if auth_admins is None or auth_admins == []:
                        kb.add(btn1)
                    else:
                        kb.row(btn1, btn2)
                    kb.add(back)

                elif param == 'tier':
                    tier = splt[2].split('=')[1]
                    gl.edit_channel_info[cid].channel_info.channel_tier = tier
                    if tier == 'SFW':
                        next_tier = 'NSFW'
                    elif tier == 'NSFW':
                        next_tier = 'OTHER'
                    elif tier == 'OTHER':
                        next_tier = 'None'
                    else:
                        next_tier = 'SFW'
                    edit_tier = telebot.types.InlineKeyboardButton("Tier: %s" % tier,
                                                                   callback_data='edit_channel=%d '
                                                                                 'editing=tier tier=%s' %
                                                                                 (editing_channel,
                                                                                  next_tier)
                                                                   ) if cid in config.BOT_SUDO else None

                    edit_main_tags = telebot.types.InlineKeyboardButton("#️⃣ Edit Tags",
                                                                        callback_data='edit_channel=%d '
                                                                                      'editing=tags' % editing_channel)

                    edit_name = telebot.types.InlineKeyboardButton("🖋 Edit Name",
                                                                   callback_data='edit_channel=%d '
                                                                                 'editing=name' % editing_channel)
                    edit_info = telebot.types.InlineKeyboardButton("💬 Edit Description",
                                                                   callback_data='edit_channel=%d '
                                                                                 'editing=description' %
                                                                                 editing_channel)
                    edit_username = telebot.types.InlineKeyboardButton("🔖 Edit Alias",
                                                                       callback_data='edit_channel=%d '
                                                                                     'editing=username' %
                                                                                     editing_channel)
                    edit_link = telebot.types.InlineKeyboardButton("🔐 Edit Private Link",
                                                                   callback_data='edit_channel=%d '
                                                                                 'editing=link' % editing_channel)

                    edit_profile_pic = telebot.types.InlineKeyboardButton("🖼 Edit Profile Pic.",
                                                                          callback_data='edit_channel=%d '
                                                                                        'editing=profile_pic' %
                                                                                        editing_channel)
                    edit_admins = telebot.types.InlineKeyboardButton("👮 Edit Admins",
                                                                     callback_data='edit_channel=%d '
                                                                                   'editing=admins' % editing_channel)
                    post_preferences = telebot.types.InlineKeyboardButton("🚀 Post Preferences",
                                                                          callback_data='edit_channel=%d '
                                                                                        'post_preferences=True' %
                                                                                        editing_channel)
                    save = telebot.types.InlineKeyboardButton("✅ Save and Exit",
                                                              callback_data='edit_channel=%d save=True' %
                                                                            editing_channel)

                    if cid in config.BOT_SUDO:
                        kb.row(edit_tier, edit_main_tags)
                    else:
                        kb.add(edit_main_tags)
                    kb.row(edit_profile_pic, edit_name)
                    kb.row(edit_username, edit_link)
                    kb.row(edit_info, edit_admins)
                    kb.add(post_preferences)
                    kb.add(save)
                    return bot.edit_message_reply_markup(chat_id=cid, message_id=call.message.message_id,
                                                         inline_message_id=call.id, reply_markup=kb)

                else:
                    gl.edit_channel_info[cid].last_msg = call.message.message_id
                    gl.edit_channel_info[cid].edit_channel = param
                    txt = Channel['editing'][param]
                    if param == 'description':
                        channel_name = gl.edit_channel_info[cid].channel_info['channel_name']
                        txt = txt.format(str((200 - 7 - len(channel_name))))
                    btn = telebot.types.InlineKeyboardButton("❌ Cancel",
                                                             callback_data='edit_channel=%d '
                                                                           'cancel=True' % editing_channel)
                    kb.add(btn)
            return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                         parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

        except Exception as e:
            from Main import GLOBAL
            import traceback
            report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data: " + str(call.data))
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


def edit_info_channel_management(bot, m, gl):
    cid = m.chat.id
    try:
        editing_info = gl.edit_channel_info[cid].edit_channel
        ch_id = int(gl.edit_channel_info[cid].channel_id)

        txt = ''
        if editing_info == 'name':
            gl.edit_channel_info[cid].channel_info['channel_name'] = m.text
            txt = 'Done! Channel Name changed.'
        if editing_info == 'description':
            channel_name = gl.edit_channel_info[cid].channel_info['channel_name']
            if m.text is None:
                mid = bot.send_message(cid, "Invalid Description: You can only use *text* for your description!\n"
                                            "Please, try again.", parse_mode='markdown')
                if 'last_msg' in gl.edit_channel_info[cid]:
                    bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)

                gl.edit_channel_info[cid].last_msg = mid.wait().message_id

                return
            elif len(m.text) > (200 - 7 - len(channel_name)):
                mid = bot.send_message(cid,
                                       "Invalid Description: Your Description can only have up to 200 characters!\n"
                                       "Please, try again.", parse_mode='markdown')
                if 'last_msg' in gl.edit_channel_info[cid]:
                    bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)

                gl.edit_channel_info[cid].last_msg = mid.wait().message_id

                return

            else:
                gl.edit_channel_info[cid].channel_info['channel_info'] = m.text
                txt = 'Done! Channel Description changed.'
        if editing_info == 'username':
            gl.edit_channel_info[cid].channel_info['channel_username'] = m.text.replace('@', '')
            txt = 'Done! Channel Alias changed.'
        if editing_info == 'link':
            gl.edit_channel_info[cid].channel_info['channel_private_link'] = m.text
            txt = 'Done! Channel Private Link changed.'
        if editing_info == 'profile_pic':
            gl.edit_channel_info[cid].channel_info['channel_profile_pic'] = m.photo[len(m.photo) - 1].file_id
            txt = 'Done! Channel Profile Picture changed.'
        if editing_info == 'tags':
            import re
            tags = re.findall("(#\w+)", m.text)
            gl.edit_channel_info[cid].channel_info['channel_tags'] = tags
            txt = 'Done! Channel Tags changed.'

        if editing_info == 'set_default_caption':
            if m.text is None:
                mid = bot.send_message(cid, "Invalid Caption: You can only use *text* for your captions!\n"
                                            "Please, try again.", parse_mode='markdown')
                if 'last_msg' in gl.edit_channel_info[cid]:
                    bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)

                gl.edit_channel_info[cid].last_msg = mid.wait().message_id

                return

            n = 198 - len(m.text)
            if n < 0:

                mid = bot.send_message(cid, "Invalid Caption: Your caption can only have up to 200 characters!\n"
                                            "Please, try again.", parse_mode='markdown')
                if 'last_msg' in gl.edit_channel_info[cid]:
                        bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)

                gl.edit_channel_info[cid].last_msg = mid.wait().message_id

                return
            else:
                gl.edit_channel_info[cid].temp_default_caption = m.text

                txt = 'Do you really want to set this as the default caption?\n\n' \
                      '💡 _Reminder: default captions will use a part of your caption, and they can not be ' \
                      'manually removed, unless the default caption is unset._\n' \
                      'Left characters for your captions: *%d*' % n

                buttons = telebot.types.InlineKeyboardMarkup(row_width=4)
                yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                callback_data="edit_channel=%d "
                                                                              "default_caption=confirm" % ch_id)
                no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                               callback_data='edit_channel=%d '
                                                                             'default_caption=set' % ch_id)
                cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                   callback_data="edit_channel=%d "
                                                                                 "default_caption=cancel" % ch_id)

                buttons.row(yes_button, no_button)
                buttons.add(cancel_button)

                bot.send_message(chat_id=cid, text=txt, reply_markup=buttons, parse_mode='markdown')

                if 'last_msg' in gl.edit_channel_info[cid]:
                    bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)
                    del gl.edit_channel_info[cid].last_msg
                return

        elif editing_info == 'set_default_reaction':
                import re
                case_test = r'([ \-\_\+\=\!\?\@\#\$\%\¨\&\*\(\)\'\"\<\
                               >\,\.\:\;\^\\/\|\w\[\]\£\¬\{\}\¹\²\³\§\~\´\`ªº    ])+'
                # link = breakpoint[1] if breakpoint[1].startswith(("http", "https", "www")) else None
                # link = breakpoint[1] if re.search(case_test, breakpoint[1]) else False

                if m.text is None or re.search(case_test, m.text) or len(m.text) > 4:
                    text = 'Invalid Reactions: You can only send emojis!\n ' \
                           'Please, send up to 4 emojis without spaces or separators, ' \
                           'as the following format:\n\n' \
                           '👌😊😔😡'
                    mid = bot.send_message(cid, text)
                    if 'last_msg' in gl.edit_channel_info[cid]:
                        bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)
                    gl.edit_channel_info[cid].last_msg = mid.wait().message_id
                    return
                temp_previews = []
                temp_reactions = []
                for i in m.text:
                    if i == '️':
                        pass
                    else:
                        temp_reactions.append(i)
                        btn = telebot.types.InlineKeyboardButton(i,
                                                                 callback_data="preview_reaction={}".format(i)
                                                                 )
                        temp_previews.append(btn)

                gl.edit_channel_info[cid].temp_reactions = temp_reactions

                buttons = telebot.types.InlineKeyboardMarkup(row_width=4)

                yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                callback_data="edit_channel=%d "
                                                                              "default_reactions=confirm" % ch_id)
                no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                               callback_data="edit_channel=%d "
                                                                             "default_reactions=set" % ch_id)
                cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                   callback_data="edit_channel=%d "
                                                                                 "default_reactions=confirm" % ch_id)

                buttons.row(*temp_previews)
                buttons.row(yes_button, no_button)
                buttons.add(cancel_button)

                txt = 'Confirm Reactions?'
                bot.send_message(chat_id=cid, text=txt, reply_markup=buttons, parse_mode='markdown')

                if 'last_msg' in gl.edit_channel_info[cid]:
                    bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)
                    del gl.edit_channel_info[cid].last_msg

                return

        gl.edit_channel_info[cid].edit_channel = True

        kb = telebot.types.InlineKeyboardMarkup(row_width=4)

        tier = gl.edit_channel_info[cid].channel_info.channel_tier
        if tier == 'SFW':
            next_tier = 'NSFW'
        elif tier == 'NSFW':
            next_tier = 'OTHER'
        elif tier == 'OTHER':
            next_tier = 'None'
        else:
            next_tier = 'SFW'
        edit_tier = telebot.types.InlineKeyboardButton("Tier: %s" % tier,
                                                       callback_data='edit_channel=%d '
                                                                     'editing=tier tier=%s' % (ch_id, next_tier)
                                                       ) if cid in config.BOT_SUDO else None

        edit_main_tags = telebot.types.InlineKeyboardButton("#️⃣ Edit Tags",
                                                            callback_data='edit_channel=%d '
                                                                          'editing=tags' % ch_id)

        edit_name = telebot.types.InlineKeyboardButton("🖋 Edit Name",
                                                       callback_data='edit_channel=%d editing=name' % ch_id)
        edit_info = telebot.types.InlineKeyboardButton("💬 Edit Description",
                                                       callback_data='edit_channel=%d editing=description' % ch_id)
        edit_username = telebot.types.InlineKeyboardButton("🔖 Edit Alias",
                                                           callback_data='edit_channel=%d editing=username' % ch_id)
        edit_link = telebot.types.InlineKeyboardButton("🔐 Edit Private Link",
                                                       callback_data='edit_channel=%d editing=link' % ch_id)

        edit_profile_pic = telebot.types.InlineKeyboardButton("🖼 Edit Profile Pic.",
                                                              callback_data='edit_channel=%d '
                                                                            'editing=profile_pic' % ch_id)
        edit_admins = telebot.types.InlineKeyboardButton("👮 Edit Admins",
                                                         callback_data='edit_channel=%d editing=admins' % ch_id)
        post_preferences = telebot.types.InlineKeyboardButton("🚀 Post Preferences",
                                                              callback_data='edit_channel=%d '
                                                                            'post_preferences=True' % ch_id)
        save = telebot.types.InlineKeyboardButton("✅ Save and Exit",
                                                  callback_data='edit_channel=%d save=True' % ch_id)

        if cid in config.BOT_SUDO:
            kb.row(edit_tier, edit_main_tags)
        else:
            kb.add(edit_main_tags)
        kb.row(edit_profile_pic, edit_name)
        kb.row(edit_username, edit_link)
        kb.row(edit_info, edit_admins)
        kb.add(post_preferences)
        kb.add(save)

        text = 'Let\'s keep editing this channel\'s info.\nHere\'s what I have:\n\n' \
               '🖼 *Channel Profile Pic.*\n {0}\n\n' \
               '🖋 *Channel Name*\n {1}\n\n' \
               '🔖 *Channel Username*\n {2}\n\n' \
               '🔐 *Channel Private Link*\n {3}\n\n' \
               '👮 *Authorized Admins*\n {4}\n\n' \
               '💬 *Channel Description* \n`{5}`\n\n' \
               '#️⃣ *Channel Tags*\n{6}\n\n' \
               '😂 *Default Reactions*\n{7}\n\n' \
               '📋 *Default Captions*\n{8}\n\n' \
               '_For this changes to be made, you must save_'

        channel = gl.edit_channel_info[cid].channel_info
        channel_admins = members.search({'authorized_channels': ch_id})
        if len(channel_admins) < 1:
            channel_admins = '_You have no authorized admins!_'
        else:
            channel_admins = ', '.join(['_%s_' % i['user_name'] for i in channel_admins])

        channel_profile_pic = channel['channel_profile_pic']
        channel_name = channel['channel_name']
        channel_description = channel['channel_info']
        channel_alias = channel['channel_username']
        channel_private_link = channel['channel_private_link']
        channel_tags = ' '.join(channel['channel_tags']).replace('_', '\_') if len(channel['channel_tags']) > 0 else \
            "_Your channel have no main tags!_"
        default_reactions = channel.get('default_reactions', None) if \
            channel.get('default_reactions', None) is not None else '_Your channel have no default Reactions!_'
        default_captions = channel.get('default_captions', None).replace("_", "\_")\
            .replace("*", "\*").replace("`", "\`") if \
            channel.get('default_captions', None) is not None else '_Your channel have no default Captions!_'

        text = text.format('/view\_\_' + channel_profile_pic.replace('_', '\_') if channel_profile_pic is not None
                           else 'None',
                           channel_name.replace('_', '\_').replace('*', '\*').replace('`', '\`') if channel_name is
                           not None else 'None',
                           '@' + channel_alias.replace('_', '\_').replace('*', '\*').replace('`', '\`') if
                           channel_alias is not None else 'None',
                           '[|Link|](' + channel_private_link + ')' if channel_private_link is not None else 'None',
                           channel_admins, channel_description, channel_tags, default_reactions, default_captions)
        text += '\n\nOwner: %s' % channel['channel_creator']['name'] if cid in config.BOT_SUDO else ''
        bot.send_message(cid, txt, parse_mode='markdown')

        if 'last_msg' in gl.edit_channel_info[cid]:
            bot.delete_message(cid, gl.edit_channel_info[cid].last_msg)
            del gl.edit_channel_info[cid].last_msg

        return bot.send_message(cid, text, parse_mode='markdown', reply_markup=kb, disable_web_page_preview=True)

    except Exception as e:
        import traceback
        report_msg(bot, m, gl, e, str(traceback.format_exc()), msg="GLOBAL: " + str(gl.edit_channel_info[cid]))
        logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
