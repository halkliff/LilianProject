import components
import telebot
import utils
from Main import queued, members, drafts, logger, channels, files, reactions, reactions_cache, analytics_main, \
    members_analytics, ch_list
# import sys
import datetime
import time
import bot_utils
import config

_posts = ['queue_posts', 'schedule_posts', 'send_posts']
bt_lst = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']

_working = []


def callback_handler(bot, call, gl):
    if call.message:
        split_data = call.data.split()
        cid = call.message.chat.id
        try:
            func = split_data[0].split('=')[0]
            arg = split_data[0].split('=')[1]

            if func in _posts:
                if func == 'queue_posts':
                    saving = bot.edit_message_text(text='🕐 Uploading Posts to the queue...', chat_id=cid,
                                                   message_id=call.message.message_id, inline_message_id=call.id)
                    kb = components.callback_kbbuttons.main_menu_admin
                    code = "%s" % utils.str_generator(4)
                    try:
                        for post in gl['create_post'][cid]['posts']:
                            if 'custom_reactions' in gl['create_post'][cid]['posts'][post]:
                                if gl['create_post'][cid]['posts'][post]['custom_reactions'] is not None:
                                    del gl['create_post'][cid]['posts'][post]['custom_reactions']['preview']
                        data = {'id': code, 'creator': call.message.chat.id,
                                'dict': gl.create_post[call.message.chat.id],
                                'date': time.mktime(datetime.datetime.utcnow().timetuple()),
                                'channel': gl.create_post[call.message.chat.id]['channel']}
                        queued.write(data)
                        members.update({'user_id': call.from_user.id}, {'$addToSet': {'queue_posts': code}})
                    except Exception as e:
                        import traceback
                        utils.report_msg(bot, call.message, gl, e, str(traceback.format_exc()), mid=saving.wait().message_id)
                        bot.send_message(call.message.chat.id, 'Your post has been saved as a draft.',
                                         reply_markup=kb(call.message.chat.id))

                        new_id = utils.str_generator(12)
                        drafts.write({"draft_id": new_id, "draft": gl.create_post[call.message.chat.id],
                                      'date': time.mktime(datetime.datetime.utcnow().timetuple())})
                        members.update({'user_id': cid}, {'$addToSet': {'drafts': new_id}})
                        logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
                        if cid in gl.create_post:
                            del gl.create_post[cid]
                        return

                    txt = 'Posts enqueued.\n\n' \
                          'You can Send it later by using the "My Posts" menu.'
                    bot.delete_message(call.message.chat.id, saving.wait().message_id)

                    bot.send_message(call.message.chat.id, txt, reply_markup=kb(call.message.chat.id))
                    if cid in gl.create_post:
                        del gl.create_post[cid]
                    return
                elif func == 'send_posts':
                    bot.delete_message(cid, call.message.message_id)
                    return components.posts.send(bot, call.message, gl, gl.create_post[call.message.chat.id])

            if func == 'report':
                code = arg
                if 'report' in gl:
                    if code in gl.report:
                        bot.send_message(196309422, gl.report[code])

                        bot.edit_message_text("Thanks. Your report has been received.", cid,
                                              call.message.message_id, call.id)
                return

            if func == 'edit_num':
                if arg == '1':
                    text = "Link Buttons Row\n\nThis is the count of how many link buttons will be in a single row," \
                           "defaults to 1, up to 4.\n\nTap ➕ to increase."

                elif arg == '4':
                    text = "Link Buttons Row\n\nThis is the count of how many link buttons will be in a single row," \
                           "defaults to 1, up to 4.\n\nTap ➖ to decrease."

                else:
                    text = "Link Buttons Row\n\nThis is the count of how many link buttons will be in a single row," \
                           "defaults to 1, up to 4.\n\nTap ➕ to increase, or ➖ to decrease."

                bot.answer_callback_query(call.id, text, show_alert=True)
                return

            if func == 'admin_channel':
                return components.management.call_channel_management(bot, call, gl, ch_list)

            if func == 'edit_channel':
                return components.management.edit_channel_management(bot, call, gl)

            if func == 'post_options':
                if 'create_post' not in gl or cid not in gl.create_post:
                    bot.delete_message(cid, call.message.message_id)
                    txt = "Error: post not cached / missing.\n\n" \
                          "_This error may be caused because the server restarted and lost the cached info " \
                          "in-memory._" \
                          "\n\nPlease, redo your post."
                    kb = components.callback_kbbuttons.main_menu_admin(cid)
                    return bot.send_message(cid, txt, reply_markup=kb, parse_mode='markdown')
                opt_func = split_data[1].split('=')[0]
                opt_arg = split_data[1].split('=')[1]

                kb = None

                txt = 'Here you are the *OPTIONS*.\n\n' \
                      'Use them to customize your posts, and avoid making the same stuff repeatedly.'
                if opt_func == 'silence_posts':
                    if opt_arg == 'True':
                        txt = '🔔 Silenced Posts:\n\n' \
                              'Select (✅) to Silence all posts made by Liliαn.\n' \
                              'Deselect (☑) to send all posts with notifications.'
                        return bot.answer_callback_query(call.id, text=txt, show_alert=True)
                    else:
                        if opt_arg == 'disable':
                            gl.create_post[cid].default_silenced = False
                        else:
                            gl.create_post[cid].default_silenced = True

                        bot.answer_callback_query(call.id, text="Done! You %sd Silent Posts." % opt_arg)
                    kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)
                if opt_func == 'web_preview':
                    if opt_arg == 'True':
                        txt = '📎 Link Previews:\n\n' \
                              'Select (✅) to enable web link previews in all posts made by Liliαn.\n' \
                              'Deselect (☑) disable web link previews.'
                        return bot.answer_callback_query(call.id, text=txt, show_alert=True)
                    else:
                        if opt_arg == 'disable':
                            gl.create_post[cid].disable_web_page_preview = False
                        else:
                            gl.create_post[cid].disable_web_page_preview = True

                        bot.answer_callback_query(call.id, text="Done! You %sd Web Page Preview." % opt_arg)
                    kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                if opt_func == 'default_caption':
                    if opt_arg == 'confirm':
                        confirm_action = split_data[2].split('=')[1]
                        if confirm_action == 'Yes':
                            import re
                            gl.create_post[cid].default_caption = gl.create_post[cid].temp_default_caption
                            tags = re.findall("(#\w+)", gl.create_post[cid].temp_default_caption)
                            gl.create_post[cid].main_tags += tags
                            del gl.create_post[cid].temp_default_caption

                            bot.answer_callback_query(call.id, text="Done! You set the Default Captions.")
                            gl.create_post[cid].queue = True
                            kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)
                        if confirm_action == 'Cancel':
                            del gl.create_post[cid].temp_default_caption
                            bot.answer_callback_query(call.id, text="You canceled. Default Captions not changed.")
                            kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                    elif opt_arg == 'set':
                        gl.create_post[cid].queue = 'set_default_caption'
                        gl.create_post[cid].last_msg = call.message.message_id
                        txt = 'Please, send the new default caption.\n\n' \
                              '💡 _Reminder: default captions will use a part of your caption, and they can not be ' \
                              'manually removed, unless the default caption is unset._'
                        kb = telebot.types.InlineKeyboardMarkup()
                        kb.add(
                            telebot.types.InlineKeyboardButton("❌ Cancel",
                                                               callback_data='post_options=True '
                                                                             'default_caption=cancel')
                        )
                    elif opt_arg == 'edit':
                        txt = 'What would you like to do with your default captions?'
                        kb = telebot.types.InlineKeyboardMarkup()
                        edit_capt = telebot.types.InlineKeyboardButton("📝 Edit",
                                                                       callback_data='post_options=True '
                                                                                     'default_caption=set')
                        del_capt = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                      callback_data='post_options=True '
                                                                                    'default_caption=delete')
                        back_menu = telebot.types.InlineKeyboardButton("🔙",
                                                                       callback_data='post_options=True back_menu=True')
                        kb.row(edit_capt, del_capt)
                        kb.add(back_menu)

                    elif opt_arg == 'delete':
                        gl.create_post[cid].default_caption = None
                        bot.answer_callback_query(call.id, text="Done! Default Captions removed.")
                        kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)
                        bot.edit_message_text(txt, cid, call.message.message_id, call.id, parse_mode='markdown',
                                              disable_web_page_preview=True, reply_markup=kb)

                        gl.create_post[cid].main_tags = channels.get({
                            'channel_id': gl.create_post[cid].channel})['channel_tags']

                        for _post in gl.create_post[cid].posts:
                            _text = _post.get('text', None)
                            _caption = _post.get('caption', None)
                            if _text is not None:
                                bot_utils.fetch_tags(cid, gl, _text, _post['id'])
                            elif _caption is not None:
                                bot_utils.fetch_tags(cid, gl, _caption, _post['id'])
                            else:
                                pass

                        return

                    elif opt_arg == 'cancel':
                        gl.create_post[cid].queue = True
                        bot.answer_callback_query(call.id, 'Operation Canceled.')
                        kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                if opt_func == 'default_reactions':
                    if opt_arg == 'confirm':
                        confirm_action = split_data[2].split('=')[1]
                        if confirm_action == 'Yes':
                            gl.create_post[cid].reactions = gl.create_post[cid].temp_reactions
                            del gl.create_post[cid].temp_reactions

                            bot.answer_callback_query(call.id, text="Done! You set the Default Reactions.")
                            gl.create_post[cid].queue = True
                            kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)
                        if confirm_action == 'Cancel':
                            del gl.create_post[cid].temp_default_caption
                            bot.answer_callback_query(call.id, text="You canceled. Default Reactions not changed.")
                            kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                    elif opt_arg == 'set':
                        gl.create_post[cid].queue = 'set_default_reaction'
                        gl.create_post[cid].last_msg = call.message.message_id
                        txt = 'Send me up to 4 emojis for the reactions without spacing or any kind of separation, ' \
                              'like the format below:\n\n' \
                              '👌😊😔😡\n\n' \
                              '💡 _Reminder: default reactions can be replaced by other reactions, although not ' \
                              'recommended, since it may break your pattern._'
                        kb = telebot.types.InlineKeyboardMarkup()
                        kb.add(
                            telebot.types.InlineKeyboardButton("❌ Cancel",
                                                               callback_data='post_options=True '
                                                                             'default_reactions=cancel')
                        )
                    elif opt_arg == 'edit':
                        txt = 'What would you like to do with your default reactions?'
                        kb = telebot.types.InlineKeyboardMarkup()
                        edit_capt = telebot.types.InlineKeyboardButton("📝 Edit",
                                                                       callback_data='post_options=True '
                                                                                     'default_reactions=set')
                        del_capt = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                      callback_data='post_options=True '
                                                                                    'default_reactions=delete')
                        back_menu = telebot.types.InlineKeyboardButton("🔙",
                                                                       callback_data='post_options=True back_menu=True')
                        kb.row(edit_capt, del_capt)
                        kb.add(back_menu)

                    elif opt_arg == 'delete':
                        gl.create_post[cid].reactions = None
                        bot.answer_callback_query(call.id, text="Done! Default Reactions removed.")
                        kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                    elif opt_arg == 'cancel':
                        gl.create_post[cid].queue = True
                        bot.answer_callback_query(call.id, 'Operation Canceled.')
                        kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                if opt_func == 'zig_zag':
                    if opt_arg == 'disable':
                        gl.create_post[cid].zig_zag = False
                    else:
                        gl.create_post[cid].zig_zag = True

                    bot.answer_callback_query(call.id, text="Done! You %sd Zig-Zag Line." % opt_arg)
                    kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                if opt_func == 'back_menu':
                    kb = components.callback_kbbuttons.main_menu_post_options(call.message, gl)

                bot.edit_message_text(txt, cid, call.message.message_id, call.id, parse_mode='markdown',
                                      disable_web_page_preview=True, reply_markup=kb)

                return

            if func == 'my_posts':
                return components.posts.my_posts_handler(bot, call)

            if func == 'queue_post':
                kb = telebot.types.InlineKeyboardMarkup(row_width=4)
                if arg == 'view':
                    view_id = split_data[1].split('=')[1]
                    n = split_data[2].split('=')[1]

                    loading = bot.edit_message_text("🕐 Loading and Rendering Posts...",
                                                    cid, call.message.message_id, call.id, parse_mode='markdown')

                    post = queued.get({'id': view_id})
                    if post is None:
                        # Something weird happened, as it should have been loaded
                        return

                    for file in post['dict']['posts']:
                        if post['dict']['posts'][file]['type'] != 'text':
                            caption = None
                            if post['dict']['default_caption'] is not None:
                                caption = post['dict'][file]['caption'] if 'caption' in post else None
                                if caption is not None:
                                    caption = '{0}\n\n{1}'.format(caption, post['dict']['default_caption'])
                                else:
                                    caption = post['dict']['default_caption']
                        else:
                            caption = None
                        bot_utils.render_post(bot, call.message, post['dict']['posts'][file], text=caption)
                        time.sleep(0.4)

                    bot.delete_message(cid, loading.wait().message_id)

                    send_btn = telebot.types.InlineKeyboardButton("🚀 Post Now",
                                                                  callback_data='queue_post=send send=%s' % view_id)
                    del_btn = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                 callback_data='queue_post=delete '
                                                                               'del=0 '
                                                                               'id=%(id)s '
                                                                               'queued=%(n)s' % {'id': view_id, 'n': n})

                    back_btn = telebot.types.InlineKeyboardButton("🔙",
                                                                  callback_data="my_posts=navigate queued=%s" % n)

                    kb.add(send_btn, del_btn)
                    kb.add(back_btn)

                    return bot.send_message(cid, "Posts Loaded.", reply_markup=kb)

                elif arg == 'send':
                    view = split_data[1].split('=')[1]
                    post = queued.get({'id': view})
                    if post is None:
                        # How?
                        return

                    components.posts.send(bot, call.message, gl, post['dict'])

                    members.update({'user_id': cid}, {'$pullAll': {'queue_posts': [view]}})
                    queued.delete({'id': view})

                    return bot.delete_message(cid, call.message.message_id)

                elif arg == 'delete':
                    """'queue_post=delete del=0 id=%s'"""
                    delete = split_data[1].split('=')[1]
                    sid = split_data[2].split('=')[1]
                    n = split_data[3].split('=')[1]

                    if delete == 'yes':
                        members.update({'user_id': cid}, {'$pullAll': {'queue_posts': [sid]}})
                        queued.delete({'id': sid})

                        txt = 'Post deleted.'

                        bot.answer_callback_query(callback_query_id=call.id, text=txt)

                        call.data = 'my_posts=navigate queued=%s' % n

                        return callback_handler(bot, call, gl)

                    else:
                        del_yes = telebot.types.InlineKeyboardButton("Yes", callback_data='queue_post=delete '
                                                                                          'del=yes '
                                                                                          'id=%(id)s '
                                                                                          'queued=%(n)s' % {'id': sid,
                                                                                                            'n': n})
                        del_no = telebot.types.InlineKeyboardButton("No", callback_data='queue_post=%(id)s '
                                                                                        'queued=%(n)s' % {'id': sid,
                                                                                                          'n': n})

                        kb.row(del_yes, del_no)

                        txt = 'Are you sure you want to delete this queued post? This action can not be undone.'

                        return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                     reply_markup=kb, parse_mode='markdown')

                else:
                    post = queued.get({'id': arg})
                    if post is None:
                        # Something weird happened, as it should have been loaded.
                        return

                    n = int(split_data[1].split('=')[1])
                    date = datetime.date.fromtimestamp(int(post['date'])).strftime("%b %d, %Y")
                    channel = channels.get({'channel_id': post['channel']})
                    txt = '📆 _%(date)s_\n\n' \
                          '*%(qtt_posts)d* posts in *%(channel_name)s*\n\n' \
                          'What are you going to do?' % {'date': date,
                                                         'qtt_posts': len(post['dict']['posts']),
                                                         'channel_name': channel['channel_name']}

                    view_btn = telebot.types.InlineKeyboardButton("👁 View",
                                                                  callback_data='queue_post=view '
                                                                                'view=%(id)s '
                                                                                'queued=%(n)s' % {'id': arg,
                                                                                                  'n': n})

                    send_btn = telebot.types.InlineKeyboardButton("🚀 Post",
                                                                  callback_data='queue_post=send send=%s' % arg)
                    del_btn = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                 callback_data='queue_post=delete '
                                                                               'del=0 '
                                                                               'id=%(id)s '
                                                                               'queued=%(n)s' % {'id': arg, 'n': n})

                    back_btn = telebot.types.InlineKeyboardButton("🔙",
                                                                  callback_data="my_posts=navigate queued=%s" % n)

                    kb.row(view_btn, send_btn, del_btn)
                    kb.add(back_btn)

                    return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                 reply_markup=kb, parse_mode='markdown')

            if func == 'draft_post':
                draft = drafts.get({'draft_id': arg})
                if draft is None:
                    # Something weird happened, as it should have been loaded.
                    return

                loading = bot.edit_message_text(text='🕐 Loading Draft...', chat_id=cid,
                                                message_id=call.message.message_id)

                to_global = utils.Dictionary(
                    {
                        'queue': True,
                        'channel': draft['draft']['channel'],
                        'disable_web_page_preview': draft['draft']['disable_web_page_preview'],
                        'default_caption': draft['draft']['default_caption'],
                        'reactions': draft['draft']['reactions'],
                        'default_silenced': draft['draft']['default_silenced'],
                        'main_tags': draft['draft']['main_tags'],
                        'posts': utils.Dictionary()
                    }
                )

                rendering = bot.edit_message_text(text='🕐 Loading and Rendering Posts...', chat_id=cid,
                                                  message_id=loading.wait().message_id)

                for post in draft['draft']['posts']:
                    p = draft['draft']['posts'][post]
                    file = None
                    if p['type'] == 'photo':
                        file = utils.Dictionary({'id': p['id'],
                                                 'creator': p['creator'],
                                                 'string': p['string'],
                                                 'type': 'photo',
                                                 'height': p['height'],
                                                 'width': p['width'],
                                                 'file_id': p['file_id'],
                                                 'caption': p['caption'],
                                                 'disable_notif': p['disable_notif'],
                                                 'custom_reactions': p['custom_reactions'],
                                                 'channel': p['channel']
                                                 }
                                                )

                    elif p['type'] == 'text':
                        file = utils.Dictionary({'id': p['id'],
                                                 'creator': p['creator'],
                                                 'string': p['string'],
                                                 'type': 'text',
                                                 'text': p['text'],
                                                 'disable_notif': p['disable_notif'],
                                                 'custom_reactions': p['custom_reactions'],
                                                 'channel': p['channel']
                                                 }
                                                )

                    elif p['type'] == 'document':
                        file = utils.Dictionary({'id': p['id'],
                                                 'creator': p['creator'],
                                                 'string': p['string'],
                                                 'type': 'document',
                                                 'file_id': p['file_id'],
                                                 'mime_type': p['mime_type'],
                                                 'caption': p['caption'],
                                                 'disable_notif': p['disable_notif'],
                                                 'custom_reactions': p['custom_reactions'],
                                                 'channel': p['channel']
                                                 }
                                                )

                    elif p['type'] == 'video':
                        file = utils.Dictionary({'id': p['id'],
                                                 'creator': p['creator'],
                                                 'string': p['string'],
                                                 'type': 'video',
                                                 'width': p['width'],
                                                 'height': p['height'],
                                                 'duration': p['duration'],
                                                 'caption': p['caption'],
                                                 'file_id': p['file_id'],
                                                 'disable_notif': p['disable_notif'],
                                                 'custom_reactions': p['custom_reactions'],
                                                 'channel': p['channel']
                                                 }
                                                )

                    if 'sauce' in p:

                        file.sauce = p['sauce']

                    if 'link_buttons' in p:
                        file.link_buttons = p['link_buttons']
                        file.row_width = p['row_width']

                    if 'custom_reactions' in p:
                        r = None
                        if p['custom_reactions'] is not None:
                            if p['custom_reactions']['reactions'] is not None:
                                r = []
                                for i in p['custom_reactions']['reactions']:
                                    t = telebot.types.InlineKeyboardButton(i,
                                                                           callback_data='preview_reaction='
                                                                                         '{}'.format(i))
                                    r.append(t)
                            p['custom_reactions']['preview'] = r

                        file.custom_reactions = p['custom_reactions']

                    to_global.posts[p['string']] = file

                gl.create_post[cid] = to_global

                txt = 'All done. You can continue editing your post.\n\n' \
                      ' _Reminder: If you Do not want to send this post now, don\'t forget to save it again as a ' \
                      'draft, or you\'ll lose all your progress!!!_'
                kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                options_btn = telebot.types.KeyboardButton("📋 Options")
                clear_all = telebot.types.KeyboardButton("🗑 Clear All")
                preview_all = telebot.types.KeyboardButton("👁 Preview")
                send_all = telebot.types.KeyboardButton("🚀 Post")
                save_draft = telebot.types.KeyboardButton("✏ Save Draft")
                cancel_post = telebot.types.KeyboardButton("❌ Cancel")

                kb.add(send_all)
                kb.row(options_btn, preview_all)
                kb.row(clear_all, save_draft)
                kb.add(cancel_post)

                bot.send_message(cid, txt, reply_markup=kb, parse_mode='markdown')

                members.update({'user_id': cid}, {'$pullAll': {'drafts': [arg]}})
                queued.delete({'draft_id': arg})

                return bot.delete_message(call.message.chat.id, rendering.wait().message_id)

            if func == 'sent_post':
                """sent_post=%s sent=1"""
                kb = telebot.types.InlineKeyboardMarkup(row_width=4)

                if arg == 'view':
                    view_id = int(split_data[1].split('=')[1])
                    n = split_data[2].split('=')[1]

                    loading = bot.edit_message_text("🕐 Loading and Rendering Posts...",
                                                    cid, call.message.message_id, call.id, parse_mode='markdown')

                    member = members.get({'user_id': cid})
                    posts = member['posts'][::-1][view_id]['posts']
                    if posts is None or posts == []:
                        # Something weird happened, as it should have been loaded
                        return

                    for post in posts:
                        file = files.get({'id': post})
                        if file is None:
                            pass
                        else:

                            """edit = telebot.types.InlineKeyboardButton("✏️Edit",
                                                                      callback_data='sent_post=edit '
                                                                                    'edit=edit '
                                                                                    'id=%(id)s '
                                                                                'sent=%(n)s' % {'id': post, 'n': n})"""
                            delete = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                        callback_data='sent_post=edit '
                                                                                      'edit=delete '
                                                                                      'id=%(id)s '
                                                                                      'sent=%(n)s '
                                                                                      'q_id=%(qid)s' % {'id': post,
                                                                                                        'n': n,
                                                                                                        'qid': view_id})
                            # kb.add(edit, delete)
                            kyb = telebot.types.InlineKeyboardMarkup()
                            kyb.add(delete)
                            bot_utils.render_post(bot, call.message, file, kyb)
                            time.sleep(0.4)

                    bot.delete_message(cid, loading.wait().message_id)

                    back_btn = telebot.types.InlineKeyboardButton("🔙",
                                                                  callback_data="my_posts=navigate sent=%s" % n)

                    kb.add(back_btn)

                    return bot.send_message(cid, "Posts Loaded.", reply_markup=kb)

                elif arg == 'edit':
                    """'sent_post=edit '
                                                                                      'edit=delete '
                                                                                      'id=%(id)s '
                                                                                      'sent=%(n)s '
                                                                                      'q_id=%(qid)s'"""

                    reason = split_data[1].split('=')[1]
                    fid = split_data[2].split('=')[1]
                    n = split_data[3].split('=')[1]
                    # This is the position of the post in the sent posts array
                    query_id = int(split_data[4].split('=')[1])

                    if reason == 'edit':
                        # TODO: Edit
                        return
                    elif reason == 'delete':
                        txt = 'Are you sure you want to delete this post from your channel?\n\n' \
                              'This action can not be undone. Will also remove the analytics for it\'s reactions, ' \
                              'if applicable.'

                        yes_btn = telebot.types.InlineKeyboardButton("Yes", callback_data='sent_post=edit '
                                                                                          'edit=delete_yes '
                                                                                          'id=%(id)s '
                                                                                          'sent=%(n)s '
                                                                                          'quid=%(q)s' % {'id': fid,
                                                                                                          'n': n,
                                                                                                          'q': query_id}
                                                                     )
                        no_btn = telebot.types.InlineKeyboardButton("No", callback_data='sent_post=edit '
                                                                                        'edit=delete_no '
                                                                                        'id=%(id)s '
                                                                                        'sent=%(n)s '
                                                                                        'quid=%(q)s' % {'id': fid,
                                                                                                        'n': n,
                                                                                                        'q': query_id})
                        kb.add(yes_btn, no_btn)
                        file = files.get({'id': fid})
                        return bot_utils.render_post(bot, call.message, file, kb, text=txt, update_message=True)

                    elif reason == 'delete_yes':
                        file = files.get({'id': fid})
                        try:

                            member_posts = members.get({'user_id': cid})['posts'][::-1]
                            pop_post = member_posts[query_id]
                            pop_post['posts'].remove(fid)

                            if pop_post['posts'] is None or pop_post['posts'] == [] or len(pop_post['posts']) < 1:
                                if len(member_posts) <= 1:
                                    member_posts = []
                                else:
                                    member_posts.remove(query_id)
                            else:
                                member_posts[query_id] = pop_post

                            members.update({'user_id': cid}, {'$set': {'posts': member_posts[::-1]}})
                            members_analytics.update({'user_id': cid}, {'$pullAll': {'posts': [fid]}})
                            reactions_cache.remove(fid)

                            files.delete({'id': fid})
                            reactions.delete({'id': fid})

                            bot.delete_message(file['channel'], file['message_id'])
                            txt = 'Post deleted.'
                            bot.answer_callback_query(call.id, txt)
                            analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'sent_deleted_posts': 1}})
                            return bot.delete_message(cid, call.message.message_id)
                        except Exception as e:
                            import traceback
                            bot.answer_callback_query(call.id, "Post couldn't be deleted.")
                            utils.report_msg(bot, call.message, gl, e, str(traceback.format_exc()))
                    elif reason == 'delete_no':
                        delete = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                    callback_data='sent_post=edit '
                                                                                  'edit=delete '
                                                                                  'id=%(id)s '
                                                                                  'sent=%(n)s '
                                                                                  'q_id=%(qid)s' % {'id': fid,
                                                                                                    'n': n,
                                                                                                    'qid': query_id})

                        kb.add(delete)
                        file = files.get({'id': fid})
                        return bot_utils.render_post(bot, call.message, file, kb, update_message=True)

                elif arg == 'delete':
                    """'queue_post=delete del=0 id=%s'"""
                    delete = split_data[1].split('=')[1]
                    sid = int(split_data[2].split('=')[1])
                    n = split_data[3].split('=')[1]

                    if delete == 'yes':

                        member_posts = members.get({'user_id': cid})['posts'][::-1]
                        pop_posts = member_posts[sid]['posts']
                        for post in pop_posts:
                            file = files.get({'id': post})
                            try:
                                bot.delete_message(file['channel'], file['message_id'])
                            except:
                                pass
                            files.delete({'id': post})
                            reactions.delete({'id': post})
                            reactions_cache.remove(post)
                            analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'sent_deleted_posts': 1}})
                            members_analytics.update({'user_id': cid}, {'$pullAll': {'posts': [post]}})

                        del member_posts[int(sid)]
                        members.update({'user_id': cid}, {'$set': {'posts': member_posts[::-1]}})

                        txt = 'Post deleted.'

                        bot.answer_callback_query(callback_query_id=call.id, text=txt)

                        call.data = 'my_posts=navigate sent=%s' % n

                        return callback_handler(bot, call, gl)

                    else:
                        del_yes = telebot.types.InlineKeyboardButton("Yes", callback_data='sent_post=delete '
                                                                                          'del=yes '
                                                                                          'id=%(id)s '
                                                                                          'sent=%(n)s' % {'id': sid,
                                                                                                          'n': n})
                        del_no = telebot.types.InlineKeyboardButton("No", callback_data='sent_post=%(id)s '
                                                                                        'sent=%(n)s' % {'id': sid,
                                                                                                        'n': n})

                        kb.row(del_yes, del_no)

                        txt = 'Are you sure you want to delete this post and all messages?\n\n' \
                              '_Doing this will remove the posts from your channel as well._'

                        return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                     reply_markup=kb, parse_mode='markdown')

                else:
                    member = members.get({'user_id': cid})
                    sent_post = member['posts'][::-1][int(arg)]
                    n = int(split_data[1].split('=')[1])
                    channel = channels.get({'channel_id': sent_post['channel']})
                    date = datetime.date.fromtimestamp(int(sent_post['date'])).strftime("%b %d, %Y")
                    txt = '📆 _%(date)s_\n\n' \
                          '*%(qtt_posts)d* posts in *%(channel_name)s*\n\n' \
                          'What are you going to do?' % {'date': date,
                                                         'qtt_posts': len(sent_post['posts']),
                                                         'channel_name': channel['channel_name']}

                    view_btn = telebot.types.InlineKeyboardButton("👁 View",
                                                                  callback_data='sent_post=view '
                                                                                'view=%(id)s '
                                                                                'sent=%(n)s' % {'id': arg,
                                                                                                'n': n})
                    del_btn = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                                 callback_data='sent_post=delete '
                                                                               'del=0 '
                                                                               'id=%(id)s '
                                                                               'sent=%(n)s' % {'id': arg, 'n': n})

                    back_btn = telebot.types.InlineKeyboardButton("🔙",
                                                                  callback_data="my_posts=navigate sent=%s" % n)

                    kb.row(view_btn, del_btn)
                    kb.add(back_btn)

                    return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                                 reply_markup=kb, parse_mode='markdown')

            if func == 'file_view':
                # TODO: File viewer



                return bot.answer_callback_query(call.id,
                                                 text="WAIT!!!\n\nWe said, it's coming soon, not ready yet >~<'")

            if func == 'preview_reaction':
                txt = 'This is the reaction for %s.\n\n' \
                      'When users tap this, it will increase or decrease, ' \
                      'depending if they have reacted or not to %s.' % (arg, arg)
                return bot.answer_callback_query(call.id, txt, show_alert=True)

            return components.posts.inline_posts_handler(bot, call, gl)

        except Exception as e:
            import traceback
            from Main import GLOBAL
            utils.report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data: " + str(call.data))
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
