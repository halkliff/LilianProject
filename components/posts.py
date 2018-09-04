import telebot
from bot_utils import send_posts, preview_posts, make_sauce, fetch_tags
import config
import re
import utils
from Main import logger, members, files, reactions, drafts, members_analytics
from Main import reactions_cache, channels, queued, analytics_main
# import sys
import components
import datetime
import time


@utils.owner_access(log=logger, db=members)
def my_posts(bot, m):
    cid = m.chat.id

    txt = 'What will you see, {name}?'.format(name=m.from_user.first_name)
    kb = telebot.types.InlineKeyboardMarkup()
    sent_posts = telebot.types.InlineKeyboardButton("Sent Posts", callback_data='my_posts=sent_posts')
    queued_posts = telebot.types.InlineKeyboardButton("Queued Posts", callback_data='my_posts=queue_posts')
    draft_posts = telebot.types.InlineKeyboardButton("Drafts", callback_data='my_posts=drafts')
    kb.row(sent_posts, queued_posts)
    kb.add(draft_posts)

    return bot.send_message(cid, txt, reply_markup=kb)


def my_posts_handler(bot, call):
    if call.message:
        cid = call.message.chat.id
        try:
            bt_lst = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']
            split_data = call.data.split()

            arg = split_data[0].split('=')[1]
            member = members.get({'user_id': call.from_user.id})
            txt = ''
            kb = telebot.types.InlineKeyboardMarkup(row_width=4)
            back = telebot.types.InlineKeyboardButton("🔙", callback_data='my_posts=back')
            if arg == 'sent_posts':
                t = member['posts'][::-1]

                if len(t) < 1:
                    txt = 'You do not have any Posts yet.'

                else:
                    txt = 'Here you are, your Posts.\n\n'
                    if len(t) > 8:
                        ct = 8
                    else:
                        ct = len(t)
                    btns = []
                    text_list = []
                    for i in range(ct):
                        btn = telebot.types.InlineKeyboardButton(bt_lst[i],
                                                                 callback_data="sent_post=%s sent=0" % i)
                        btns.append(btn)
                        prep = '%(p_id)s *%(qtt_posts)s* Posts to *%(channel)s* | _%(date)s_' % {
                            'p_id': bt_lst[i],
                            'date': datetime.date.fromtimestamp(int(t[i]['date'])).strftime("%b %d"),
                            'qtt_posts': len(t[i]['posts']),
                            'channel': channels.get({'channel_id': t[i]['channel']})['channel_name']
                        }
                        text_list.append(prep)

                    kb.add(*btns)

                    txt += '\n'.join(text_list)

                    if len(t) > 8:  # Have more than 8 queued posts
                        next_button = telebot.types.InlineKeyboardButton("▶️",
                                                                         callback_data="my_posts=navigate sent=1")
                        kb.add(next_button)
                kb.add(back)

            if arg == 'queue_posts':
                t = member['queue_posts'][::-1]

                if len(t) < 1:
                    txt = 'You do not have any Queued posts.'

                else:
                    txt = 'Here you are, your Queued Posts.\n\n'
                    if len(t) > 8:
                        ct = 8
                    else:
                        ct = len(t)
                    btns = []
                    text_list = []
                    for i in range(ct):
                        btn = telebot.types.InlineKeyboardButton(bt_lst[i],
                                                                 callback_data="queue_post=%s queued=0" % t[i])
                        btns.append(btn)
                        queue_posts = queued.get({'id': t[i]})
                        prep = '%(p_id)s *%(channel)s:* *%(qtt_posts)s* Posts | _%(date)s_' % {
                            'p_id': bt_lst[i],
                            'date': datetime.date.fromtimestamp(int(queue_posts['date'])).strftime("%b %d"),
                            'qtt_posts': len(queue_posts['dict']['posts']),
                            'channel': channels.get({'channel_id': queue_posts['dict']['channel']})['channel_name']
                        }
                        text_list.append(prep)

                    kb.add(*btns)

                    txt += '\n'.join(text_list)

                    if len(t) > 8:  # Have more than 8 queued posts
                        next_button = telebot.types.InlineKeyboardButton("▶️",
                                                                         callback_data="my_posts=navigate queued=1")
                        kb.add(next_button)
                kb.add(back)

            if arg == 'drafts':
                t = member['drafts'][::-1]
                if len(t) < 1:
                    txt = 'You do not have any Drafts.'

                else:
                    txt = 'Here you are your Drafts list.\n\n'

                    if len(t) > 8:
                        ct = 8
                    else:
                        ct = len(t)
                    btns = []
                    text_list = []
                    for i in range(ct):
                        btn = telebot.types.InlineKeyboardButton(bt_lst[i],
                                                                 callback_data="draft_post=%s drafts=0" % t[i])
                        btns.append(btn)
                        draft_post = drafts.get({'draft_id': t[i]})
                        prep = '%(p_id)s Draft for *%(channel)s* | _%(date)s_' % {
                            'p_id': bt_lst[i],
                            'date': datetime.date.fromtimestamp(int(draft_post['date'])).strftime("%b %d"),
                            'channel': channels.get({'channel_id': draft_post['draft']['channel']})['channel_name']
                        }
                        text_list.append(prep)

                    kb.add(*btns)

                    txt += '\n'.join(text_list)

                    if len(t) > 8:  # Have more than 8 drafts
                        next_button = telebot.types.InlineKeyboardButton("▶️",
                                                                         callback_data="my_posts=navigate drafts=1")
                        kb.add(next_button)
                kb.add(back)

            if arg == 'back':
                txt = 'What will you see, {name}?'.format(name=call.from_user.first_name)
                kb = telebot.types.InlineKeyboardMarkup()
                sent_posts = telebot.types.InlineKeyboardButton("Sent Posts", callback_data='my_posts=sent_posts')
                queued_posts = telebot.types.InlineKeyboardButton("Queued Posts", callback_data='my_posts=queue_posts')
                draft_posts = telebot.types.InlineKeyboardButton("Drafts", callback_data='my_posts=drafts')
                kb.row(sent_posts, queued_posts)
                kb.add(draft_posts)

            if arg == 'navigate':
                _type = split_data[1].split('=')[0]
                n = int(split_data[1].split('=')[1])
                btns = []
                if _type == 'queued':
                    queued_posts = member['queue_posts'][::-1]
                    posts = queued_posts
                    aut_num = 8 * n
                    auth = queued_posts[aut_num:]
                    if len(posts) < 1:
                        txt = 'You do not have any Queued posts.'

                    else:
                        txt = 'Here you are, your Queued Posts.\n\n'

                elif _type == 'drafts':
                    draft_posts = member['drafts'][::-1]
                    posts = draft_posts
                    aut_num = 8 * n
                    auth = draft_posts[aut_num:]
                    if len(posts) < 1:
                        txt = 'You do not have any Drafts.'

                    else:
                        txt = 'Here you are your Drafts list.\n\n'

                elif _type == 'sent':

                    sent_posts = member['posts'][::-1]
                    posts = sent_posts
                    aut_num = 8 * n
                    auth = sent_posts[aut_num:]
                    if len(posts) < 1:
                        txt = 'You do not have any Posts yet.'

                    else:
                        txt = 'Here you are, your Posts.\n\n'

                else:
                    raise AttributeError

                if len(auth) > 8:
                    ct = 8
                else:
                    ct = len(auth)
                text_list = []
                for i in range(ct):
                    btn = telebot.types.InlineKeyboardButton(bt_lst[i],
                                                             callback_data="%s=%s %s=%s" % ('queue_post' if
                                                                                            _type == 'queued' else
                                                                                            'draft_post' if
                                                                                            _type == 'draft_post' else
                                                                                            'sent_post', (aut_num + i)
                                                                                            if
                                                                                            _type == 'sent'
                                                                                            else auth[i],
                                                                                            _type, n))

                    if _type == 'queued':
                        queue_posts = queued.get({'id': auth[i]})
                        ls = {
                            'p_id': bt_lst[i],
                            'date': datetime.date.fromtimestamp(int(queue_posts['date'])).strftime("%b %d"),
                            'qtt_posts': len(queue_posts['dict']['posts']),
                            'channel': channels.get({'channel_id': queue_posts['dict']['channel']})['channel_name']
                        }
                        prep = '%(p_id)s *%(channel)s:* *%(qtt_posts)s* Posts | _%(date)s_'
                    elif _type == 'draft':
                        draft_post = drafts.get({'draft_id': auth[i]})
                        ls = {
                            'p_id': bt_lst[i],
                            'date': datetime.date.fromtimestamp(int(draft_post['date'])).strftime("%b %d"),
                            'channel': channels.get({'channel_id': draft_post['draft']['channel']})['channel_name']
                        }
                        prep = '%(p_id)s Draft for *%(channel)s* | _%(date)s_'
                    elif _type == 'sent':
                        ls = {
                            'p_id': bt_lst[i],
                            'date': datetime.date.fromtimestamp(int(auth[i]['date'])).strftime("%b %d"),
                            'qtt_posts': len(auth[i]['posts']),
                            'channel': channels.get({'channel_id': auth[i]['channel']})['channel_name']
                        }
                        prep = '%(p_id)s *%(qtt_posts)s* Posts to *%(channel)s* | _%(date)s_'
                    else:
                        ls = {
                            'p_id': bt_lst[i],
                        }
                        prep = '%(p_id)s `UNKNOWN ERROR`'

                    prep = prep % ls
                    text_list.append(prep)
                    btns.append(btn)

                txt += '\n'.join(text_list)

                next_button = telebot.types.InlineKeyboardButton("▶️",
                                                                 callback_data="my_posts=navigate "
                                                                               "%s=%s" % (_type, n + 1))
                previous_button = telebot.types.InlineKeyboardButton("◀️",
                                                                     callback_data="my_posts=navigate "
                                                                                   "%s=%s" % (_type, n - 1))

                kb.add(*btns)
                if n == 0 and len(posts) <= 8:
                    pass

                else:
                    if len(posts) <= 8 * (n + 1):
                        kb.add(previous_button)

                    elif len(posts) > (8 * (n + 1)) and n - 1 >= 0:
                        kb.add(previous_button, next_button)

                    else:
                        kb.add(next_button)

                kb.add(back)
                # return bot.edit_message_reply_markup(cid, call.message.message_id, call.id, reply_markup=kb)

            return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                         reply_markup=kb, parse_mode='markdown')
        except Exception as e:
            import traceback
            from Main import GLOBAL
            utils.report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data: " + call.data)
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


@utils.owner_access(log=logger, db=members)
def new_post(bot, m, ch_list):
    cid = m.chat.id
    try:
        msg = 'Tap a button below to select a channel to post:'

        kb = telebot.types.InlineKeyboardMarkup(row_width=2)
        btns = []
        """if cid in config.BOT_SUDO:
            for item in ch_list:
                btn = telebot.types.InlineKeyboardButton(item['channel_name'],
                                                         callback_data="new_post={}".format(item['channel_id']))
                btns.append(btn)
    
            next_button = telebot.types.InlineKeyboardButton("▶️", callback_data="next_channels=1")
    
            kb.add(*btns)
    
            if len(ch_list) > 1:
                kb.add(next_button)
    
            keyb = telebot.types.InlineKeyboardMarkup(row_width=3)
            t = telebot.types.InlineKeyboardButton("Test", callback_data="new_post=-1001132758250")
            keyb.add(t)
    
            return bot.send_message(cid, msg, reply_markup=keyb)
            auth_channels = ch_list

        else:"""
        member = members.get({'user_id': cid})
        a_channels = member['owned_channels'] + member['authorized_channels']

        if len(a_channels) < 1:
            txt = 'You do now own or are authorized to post in any channel!\n\n' \
                      'Tap the button below if you wish to add a channel.'
            add_channel = telebot.types.InlineKeyboardButton("➕ Add a Channel",
                                                             callback_data='admin_channel=add_channel')
            kb.add(add_channel)

            return bot.send_message(chat_id=cid, text=txt, reply_markup=kb)

        auth_channels = []
        for i in a_channels:
            ch = channels.get({'channel_id': i})
            auth_channels.append(ch)

        if len(auth_channels) > 6:
            ct = 6
        else:
            ct = len(auth_channels)

        for i in range(ct):
            btn = telebot.types.InlineKeyboardButton(auth_channels[i]['channel_name'],
                                                     callback_data="new_post=%s" % auth_channels[i]['channel_id'])
            btns.append(btn)

        kb.add(*btns)

        if ct == 6:  # Have more than 6 channels
            next_button = telebot.types.InlineKeyboardButton("▶️", callback_data="next_channels=1")
            kb.add(next_button)

        return bot.send_message(cid, msg, reply_markup=kb)
    except Exception as e:
        from Main import GLOBAL
        import traceback
        utils.report_msg(bot, m, GLOBAL, e, str(traceback.format_exc()), msg="Func: new post")
        logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))


@utils.owner_access(log=logger, db=members)
def send(bot, m, gl, posts_dict):
    cid = m.chat.id

    loading = bot.send_message(cid, "🕐 Uploading Posts in database...")
    kb = components.callback_kbbuttons.main_menu_admin

    safe = posts_dict
    posts = posts_dict['posts']

    try:
        for post in posts:
            r = None
            if 'custom_reactions' in posts[post]:
                if posts[post]['custom_reactions'] is not None:
                    if posts[post]['custom_reactions']['reactions'] is not None:
                        r = utils.Dictionary()
                        c = 1
                        for i in posts[post]['custom_reactions']['reactions']:
                            r.update({'p{}'.format(c): i})
                            c += 1

                    elif safe['reactions'] is not None:
                        r = utils.Dictionary()
                        c = 1
                        for i in safe['reactions']:
                            r.update({'p{}'.format(c): i})
                            c += 1

                    del posts[post]['custom_reactions']

            posts[post]['reactions'] = r
            posts[post]['message_id'] = None
            if 'caption' in posts[post]:
                if posts_dict['default_caption'] is not None:
                    if posts[post]['caption'] is not None:
                        posts[post]['caption'] = '{0}\n\n{1}'.format(posts[post]['caption'],
                                                                     posts_dict['default_caption'])
                    else:
                        posts[post]['caption'] = posts_dict['default_caption']
            files.update({'id': posts[post]['id']}, {'$set': posts[post]})
            if r is not None:
                reactions_file = {'id': posts[post]['id'],
                                  'reactions': {i: {'em': r[i], 'count': 0} for i in r},
                                  'reaction_list': {}
                                  }
                reactions.write(reactions_file)
    except Exception as e:
        import traceback
        utils.report_msg(bot, m, gl, e, str(traceback.format_exc()), mid=loading.wait().message_id)
        bot.send_message(cid, 'Your post has been saved as a draft.', reply_markup=kb(cid))

        new_id = utils.str_generator(12)
        for post in safe['posts']:
            if 'custom_reactions' in safe['posts'][post]:
                del safe['posts'][post]['custom_reactions']['preview']
        drafts.write({"draft_id": new_id, "draft": safe, 'date': time.mktime(datetime.datetime.utcnow().timetuple())})
        members.update({'user_id': cid}, {'$addToSet': {'drafts': new_id}})
        logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))

        if cid in gl.create_post:
            del gl.create_post[cid]
        del safe
        del posts

        return

    posting = bot.edit_message_text("🕐 Done. Sending posts...", cid, loading.wait().message_id)

    post_row = {'channel': safe['channel'],
                'date': time.mktime(datetime.datetime.utcnow().timetuple()),
                'posts': []}
    inc = 0
    if 'zig_zag' in posts_dict:
        if posts_dict['zig_zag']:
            bot.send_message(posts_dict['channel'], '〰〰〰〰〰〰〰〰〰〰〰〰').wait()
    for post in posts:
        wp_preview = safe['disable_web_page_preview']
        disable_notif = posts[post]['disable_notif'] if not safe['default_silenced'] else safe['default_silenced']
        post_reactions = None
        if posts[post]['reactions'] is not None:
            post_reactions = []
            for i in posts[post]['reactions']:

                call_data = "reaction={0}&{1}".format(posts[post]['id'], i)
                btn = telebot.types.InlineKeyboardButton(posts[post]['reactions'][i] + ' 0', callback_data=call_data)
                post_reactions.append(btn)

        mid = send_posts(bot, safe, posts[post], post_reactions, wp_preview, disable_notif)
        files.update(
            {'id': posts[post]['id']},
            {
                '$set':
                    {
                        'message_id': mid,
                        'date_time': time.mktime(datetime.datetime.utcnow().timetuple())
                    }
            }
        )

        if post_reactions is not None:
            cache = {}
            if 'link_buttons' in posts[post]:
                cache.update({'link_buttons': posts[post]['link_buttons'], 'row_width': posts[post]['row_width']})

            if 'sauce' in posts[post]:
                cache.update({'sauce': posts[post]['sauce']})
            reactions_cache.add(posts[post]['id'], cache, 4 * 60 * 60)

        members_analytics.update({'user_id': cid}, {'$addToSet': {'posts': posts[post]['id']}})
        members_analytics.update({'user_id': cid}, {'$inc': {'all_time_posts': 1}})
        post_row['posts'].append(posts[post]['id'])
        inc += 1

        if inc == 10:
            time.sleep(5)
            inc = 0
        time.sleep(1.5)

        analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'sent_posts': 1}})

    bot.delete_message(cid, posting.wait().message_id)
    bot.send_message(cid, "All posts sent.", reply_markup=kb(cid))

    if cid in gl.create_post:
        del gl.create_post[cid]
    del safe
    del posts
    members.update({'user_id': m.chat.id}, {'$addToSet': {'posts': post_row}})
    del post_row
    return


def posts_handler(bot, m, gl, files_main):
    cid = m.chat.id

    if cid in gl.create_post:
        if 'queue' in gl.create_post[cid]:
            if gl.create_post[cid].queue == 'waiting_buttons_row':
                file = str(gl.create_post[cid].waiting_post)
                post = gl.create_post[cid].posts[file]
                test_case = r'([\w.\-\+\=\*\!\?\~\^\[\]\{\}\\\/\@\#\$\%\&\(\)\_ \uD800-\uDBFF]+|' \
                            r'[\w.\-\+\=\*\!\?\~\^\[\]\{\}\\\/\@\#\$\%\&\(\)\_ \u2702-\u27B0]+' \
                            r'|[\w.\-\+\=\*\!\?\~\^\[\]\{\}\\\/\@\#\$\%\&\(\)\_ \uF680-\uF6C0]+|' \
                            r'[\w.\-\+\=\*\!\?\~\^\[\]\{\}\\\/\@\#\$\%\&\(\)\_ \u24C2-\uF251]+)' \
                            r'([-] )(([h-t]+:\/\/+[\w.\/?=&\-]+)|([\w.\/\-]+)(\.[\w\/?=&\-]+))'
                broken = m.text.split('\n')
                links = []
                for i in broken:
                    match = re.search(test_case, i)
                    if match:
                        links.append(i)

                    else:
                        text = "*Invalid format:*\n`{}`\n\nThe correct format is:\n" \
                               "`Name 1 - link1`\n`Name 2 - link2`\n\nFix this before we continue.".format(i)
                        bot.send_message(cid, text, parse_mode='markdown')
                        links = []
                        break

                if len(links) >= 1:
                    pv_buttons = []
                    buttons = []
                    for i in links:
                        splt = i.split(' - ')
                        link_name = splt[0]
                        link_url = splt[1]
                        b = {'label_text': link_name, 'url': link_url}
                        button = telebot.types.InlineKeyboardButton(text=link_name, url=link_url)
                        pv_buttons.append(button)
                        buttons.append(b)
                    if 'link_buttons' in gl.create_post[cid].posts[file]:
                        gl.create_post[cid].posts[file].temp_link_buttons = buttons
                        gl.create_post[cid].posts[file].temp_row_width = 1
                    else:
                        gl.create_post[cid].posts[file].link_buttons = buttons
                        gl.create_post[cid].posts[file].row_width = 1

                    buttons = telebot.types.InlineKeyboardMarkup(row_width=3)

                    plus_button = telebot.types.InlineKeyboardButton(text="➕",
                                                                     callback_data='plus_link={}'.format(file))
                    num_row_button = telebot.types.InlineKeyboardButton(text="1", callback_data="edit_num=1")
                    ok_button = telebot.types.InlineKeyboardButton(text='👌🏼 Ok!',
                                                                   callback_data='ok_link={}'.format(file))

                    yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                    callback_data="link_yes={}".format(file))
                    no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                                   callback_data="link_no={}".format(file))
                    cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                       callback_data="link_cancel={}".format(file))

                    for button in pv_buttons:
                        buttons.add(button)

                    if len(links) == 1:
                        buttons.row(yes_button, no_button)
                        buttons.add(cancel_button)
                        text = 'Confirm this link button?'
                    else:
                        buttons.row(num_row_button, plus_button)
                        buttons.add(ok_button)

                        text = 'Now, please select how many buttons would you like in a row.'

                    preview_posts(bot, gl, m, file=[post], buttons=buttons, caption=text, custom_caption=True)
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)
                        del gl.create_post[cid].last_msg

                    gl.create_post[cid].queue = True
                return

            elif gl.create_post[cid].queue == 'waiting_new_caption':
                file = str(gl.create_post[cid].waiting_post)
                gl.create_post[cid].posts[file].caption = m.text
                post = gl.create_post[cid].posts[file]

                preview_posts(bot, gl, m, file=[post])
                fetch_tags(cid, gl, m.text, file)
                gl.create_post[cid].queue = True
                del gl.create_post[cid].waiting_post
                if 'last_msg' in gl.create_post[cid]:
                    bot.delete_message(cid, gl.create_post[cid].last_msg)
                    del gl.create_post[cid].last_msg
                return

            elif gl.create_post[cid].queue == 'waiting_new_text':
                file = str(gl.create_post[cid].waiting_post)
                gl.create_post[cid].posts[file].text = m.text
                post = gl.create_post[cid].posts[file]

                preview_posts(bot, gl, m, file=[post])
                gl.create_post[cid].queue = True
                fetch_tags(cid, gl, m.text, file)
                del gl.create_post[cid].waiting_post
                if 'last_msg' in gl.create_post[cid]:
                    bot.delete_message(cid, gl.create_post[cid].last_msg)
                    del gl.create_post[cid].last_msg
                return

            elif gl.create_post[cid].queue == 'waiting_sauce':
                file = str(gl.create_post[cid].waiting_post)
                try:
                    post = gl.create_post[cid].posts[file]

                    make_sauce(m.text, post, from_text=True)

                    buttons = telebot.types.InlineKeyboardMarkup(row_width=3)
                    yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                    callback_data="sauce_yes={}".format(file))
                    no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                                   callback_data="sauce_no={}".format(file))
                    cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                       callback_data="sauce_cancel={}".format(file))
                    # {'label_text': "Source: [{}]".format(source_name.title()), 'url': link}
                    sauce_btn = telebot.types.InlineKeyboardButton(post.sauce['label_text'], url=post.sauce['url'])
                    buttons.add(sauce_btn)
                    buttons.row(yes_button, no_button)
                    buttons.add(cancel_button)
                    text = 'Confirm this Sauce?'

                    preview_posts(bot, gl, m, file=[post], buttons=buttons, caption=text, custom_caption=True)
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)
                        del gl.create_post[cid].last_msg

                except AttributeError:
                    text = "*Invalid format:*\n`{}`\n\nThe correct format is:\n" \
                           "`Sauce - id/Link`\n\nThe available sauces are:\n" \
                           "Pixiv, Gelbooru, Danbooru, Safebooru, Sankaku, Konachan, Yandere\n\n" \
                           "Fix this before we continue.".format(m.text)
                    bot.send_message(cid, text, parse_mode='markdown')

                return

            elif gl.create_post[cid].queue == 'waiting_reactions_row':
                file = str(gl.create_post[cid].waiting_post)
                post = gl.create_post[cid].posts[file]

                case_test = r'([ \-\_\+\=\!\?\@\#\$\%\¨\&\*\(\)\'\"\<\
                >\,\.\:\;\^\\/\|\w\[\]\£\¬\{\}\¹\²\³\§\~\´\`ªº    ])+'
                # link = breakpoint[1] if breakpoint[1].startswith(("http", "https", "www")) else None
                # link = breakpoint[1] if re.search(case_test, breakpoint[1]) else False
                if re.search(case_test, m.text):
                    text = 'Invalid Reactions: You can only send emojis!\n ' \
                           'Please, send up to 4 emojis without spaces or separators, ' \
                           'as the following format:\n\n' \
                           '👌😊😔😡'
                    mid = bot.send_message(cid, text)
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)

                    gl.create_post[cid].last_msg = mid.wait().message_id
                    return
                temp_previews = []
                temp_reactions = []
                x = 0
                for i in m.text:
                    if i == '️':
                        pass
                    else:
                        temp_reactions.append(i)
                        btn = telebot.types.InlineKeyboardButton(i,
                                                                 callback_data="preview_reaction={}".format(i)
                                                                 )
                        temp_previews.append(btn)
                        x += 1

                if x > 4:
                    text = 'Invalid Reactions: You can only send up to 4 emojis!\n ' \
                           'Please, send up to 4 emojis without spaces or separators, ' \
                           'as the following format:\n\n' \
                           '👌😊😔😡'
                    mid = bot.send_message(cid, text)
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)

                    gl.create_post[cid].last_msg = mid.wait().message_id
                    return
                if post['custom_reactions'] is None:
                    post['custom_reactions'] = utils.Dictionary({'preview': None, 'reactions': None})
                post['custom_reactions']['temp'] = {'preview': temp_previews, 'reactions': temp_reactions}

                buttons = telebot.types.InlineKeyboardMarkup(row_width=4)

                yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                callback_data="reactions_yes={}".format(file))
                no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                               callback_data="reactions_no={}".format(file))
                cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                   callback_data="reactions_cancel={}".format(file))

                buttons.row(*temp_previews)
                buttons.row(yes_button, no_button)
                buttons.add(cancel_button)

                text = 'Confirm Reactions?'

                preview_posts(bot, gl, m, file=[post], buttons=buttons, caption=text, custom_caption=True)
                if 'last_msg' in gl.create_post[cid]:
                    bot.delete_message(cid, gl.create_post[cid].last_msg)
                    del gl.create_post[cid].last_msg

                return

            elif gl.create_post[cid].queue == 'set_default_caption':
                if m.text is None:
                    mid = bot.send_message(cid, "Invalid Caption: You can only use *text* for your captions!\n"
                                                "Please, try again.")
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)

                    gl.create_post[cid].last_msg = mid.wait().message_id

                    return

                n = 198 - len(m.text)
                if n < 0:

                    mid = bot.send_message(cid, "Invalid Caption: Your caption can only have up to 200 characters!\n"
                                                "Please, try again.")
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)

                    gl.create_post[cid].last_msg = mid.wait().message_id

                    return
                else:
                    gl.create_post[cid].temp_default_caption = m.text

                    txt = 'Do you really want to set this as the default caption?\n\n' \
                          '💡 _Reminder: default captions will use a part of your caption, and they can not be ' \
                          'manually removed, unless the default caption is unset._\n' \
                          'Left characters for your captions: *%d*' % n

                    buttons = telebot.types.InlineKeyboardMarkup(row_width=4)
                    yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                    callback_data="post_options=True "
                                                                                  "default_caption=confirm "
                                                                                  "confirm=Yes")
                    no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                                   callback_data='post_options=True '
                                                                                 'default_caption=set')
                    cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                       callback_data="post_options=True "
                                                                                     "default_caption=confirm "
                                                                                     "confirm=Cancel")

                    buttons.row(yes_button, no_button)
                    buttons.add(cancel_button)

                    bot.send_message(chat_id=cid, text=txt, reply_markup=buttons, parse_mode='markdown')

                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)
                        del gl.create_post[cid].last_msg

            elif gl.create_post[cid].queue == 'set_default_reaction':
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
                    if 'last_msg' in gl.create_post[cid]:
                        bot.delete_message(cid, gl.create_post[cid].last_msg)
                    gl.create_post[cid].last_msg = mid.wait().message_id
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

                gl.create_post[cid].temp_reactions = temp_reactions

                buttons = telebot.types.InlineKeyboardMarkup(row_width=4)

                yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                                callback_data="post_options=True "
                                                                              "default_reactions=confirm confirm=Yes")
                no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                               callback_data="post_options=True default_reactions=set")
                cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                                   callback_data="post_options=True "
                                                                                 "default_reactions=confirm "
                                                                                 "confirm=Cancel")

                buttons.row(*temp_previews)
                buttons.row(yes_button, no_button)
                buttons.add(cancel_button)

                txt = 'Confirm Reactions?'
                bot.send_message(chat_id=cid, text=txt, reply_markup=buttons, parse_mode='markdown')

                if 'last_msg' in gl.create_post[cid]:
                    bot.delete_message(cid, gl.create_post[cid].last_msg)
                    del gl.create_post[cid].last_msg

            else:
                string = utils.str_generator(12)
                try:
                    post_list = gl.create_post[cid].posts

                    post_quantity = files_main.get({'_id': config.FILES_MAIN})['created_posts']

                    sid = utils.id_encoder(post_quantity + 1)

                    caption = m.caption

                    # This variable is to tell if the post was made or not. Default to False, due to the last if.
                    f = False
                    reaction = gl.create_post[cid].reactions

                    if m.content_type == 'photo':
                        post_list[string] = utils.Dictionary({'id': sid,
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
                    logger.error(e)

    if 'edit_sent_post' in gl:
        if cid in gl.edit_sent_post:
            if m.forward_from_chat is None:
                pass
                # This means the message wasn't forwarded, and must not continue with the authentication.
            if m.forward_from_chat.type != 'channel':
                pass
                # Didn't come from a channel, fail the authentication

            channel_id = m.forward_from_chat.id

            channel = channels.get({'channel_id': channel_id})
            if channel is None:
                pass
                # Channel is not in our database, fail the authentication

            post = files.get({'message_id': 32, 'channel': channel['channel_id']})
            if post is None:
                # Post not in the database,
                pass
            if gl.edit_sent_post[cid].queue == 'edit':
                pass

            if gl.edit_sent_post[cid].queue == 'delete':
                if m.forward_from_chat is None:
                    pass
                    # This means the message wasn't forwarded, and must not continue with the authentication.


def inline_posts_handler(bot, call, gl):
    cid = call.message.chat.id
    split_data = call.data.split()

    func = split_data[0].split('=')[0]
    file = split_data[0].split('=')[1]

    if cid not in gl.create_post or file not in gl.create_post[cid].posts:
        bot.answer_callback_query(call.id, "This post was removed earlier.")
        bot.delete_message(cid, call.message.message_id)
        return False

    cancel = telebot.types.InlineKeyboardMarkup(row_width=1)
    btn = telebot.types.InlineKeyboardButton("❌ Cancel", callback_data='cancel={}'.format(file))
    cancel.add(btn)

    if func == 'back_editing':
        preview_posts(bot, gl, call.message, [gl.create_post[cid].posts[file]], update_message=True)

    if func == 'preview_post':
        preview_posts(bot, gl, call.message, [gl.create_post[cid].posts[file]], update_message=True, preview_only=True)

    if func == 'plus_link' or func == 'minus_link' or func == 'ok_link':
        post = gl.create_post[cid].posts[file]
        if 'temp_row_width' in post:
            num = int(post.temp_row_width)
        else:
            num = int(post.row_width)

        plus_button = telebot.types.InlineKeyboardButton(text="➕",
                                                         callback_data='plus_link={}'.format(file))
        minus_button = telebot.types.InlineKeyboardButton(text="➖",
                                                          callback_data='minus_link={}'.format(file))
        ok_button = telebot.types.InlineKeyboardButton(text='👌🏼 Ok!', callback_data='ok_link={}'.format(file))

        yes_button = telebot.types.InlineKeyboardButton(text="✔️ Confirm",
                                                        callback_data="link_yes={}".format(file))
        no_button = telebot.types.InlineKeyboardButton(text="✖️ Redo ",
                                                       callback_data="link_no={}".format(file))
        cancel_button = telebot.types.InlineKeyboardButton(text='❌ Cancel',
                                                           callback_data="link_cancel={}".format(file))
        if func == 'plus_link':
            num += 1
            if 'temp_row_width' in post:
                post.temp_row_width = num
                links = post.temp_link_buttons
            else:
                post.row_width = num
                links = post.link_buttons
            btns = []
            for i in links:
                btn = telebot.types.InlineKeyboardButton(i['label_text'], url=i['url'])
                btns.append(btn)
            buttons = telebot.types.InlineKeyboardMarkup(row_width=num)
            buttons.add(*btns)

            num_row_button = telebot.types.InlineKeyboardButton(text="{}".format(num),
                                                                callback_data="edit_num={}".format(num))
            if num == 4:
                buttons.row(minus_button, num_row_button)
            else:
                buttons.row(minus_button, num_row_button, plus_button)
            buttons.add(ok_button)

            bot.edit_message_reply_markup(cid, call.message.message_id, call.id, reply_markup=buttons)

        elif func == 'minus_link':
            num -= 1

            if 'temp_row_width' in post:
                post.temp_row_width = num
                links = post.temp_link_buttons
            else:
                post.row_width = num
                links = post.link_buttons
            btns = []
            for i in links:
                btn = telebot.types.InlineKeyboardButton(i['label_text'], url=i['url'])
                btns.append(btn)
            buttons = telebot.types.InlineKeyboardMarkup(row_width=num)
            buttons.add(*btns)

            num_row_button = telebot.types.InlineKeyboardButton(text="{}".format(num),
                                                                callback_data="edit_num={}".format(num))
            if num == 1:
                buttons.row(num_row_button, plus_button)
            else:
                buttons.row(minus_button, num_row_button, plus_button)

            buttons.add(ok_button)
            bot.edit_message_reply_markup(cid, call.message.message_id, call.id, reply_markup=buttons)

        elif func == 'ok_link':
            if 'temp_row_width' in post:
                num = post.temp_row_width
                links = post.temp_link_buttons
            else:
                num = post.row_width
                links = post.link_buttons
            btns = []
            for i in links:
                btn = telebot.types.InlineKeyboardButton(i['label_text'], url=i['url'])
                btns.append(btn)
            buttons = telebot.types.InlineKeyboardMarkup(row_width=num)
            buttons.add(*btns)

            buttons.row(yes_button, no_button)
            buttons.add(cancel_button)
            text = "Confirm these link buttons?"
            preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                          update_message=True, caption=text, buttons=buttons, custom_caption=True)

    if func == 'off_notif':
        # Disable the notifications by parsing it True
        gl.create_post[cid].posts[file].disable_notif = True
        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]], update_message=True)

    if func == 'on_notif':
        # Enable the notifications by parsing it False
        gl.create_post[cid].posts[file].disable_notif = False
        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]], update_message=True)

    if func == 'edit_caption':
        gl.create_post[cid].queue = 'waiting_new_caption'
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = 'Send the new caption to be inserted in this file.'
        analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'edited_posts': 1}})

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'edit_text':
        gl.create_post[cid].queue = 'waiting_new_text'
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'edited_posts': 1}})
        text = 'Send the new text.'

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'add_sauce':
        gl.create_post[cid].queue = 'waiting_sauce'
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = 'Send the sauce and it\'s ID or Link. The available sauces are:\n\n' \
               'Pixiv, Gelbooru, Danbooru, Safebooru, Sankaku, Konachan, Yandere\n\n' \
               'To send, use:\n' \
               'Sauce - id/Link'

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'add_link':
        gl.create_post[cid].queue = 'waiting_buttons_row'
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = 'Send your links in the following format:\n\n' \
               'Name 1 - link1\nName 2 - link2'

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'edit_sauce':
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = "What would you like to do?"
        sbtn = telebot.types.InlineKeyboardMarkup(row_width=3)
        b1 = telebot.types.InlineKeyboardButton("📝 Edit Sauce", callback_data="add_sauce={}".format(file))
        b2 = telebot.types.InlineKeyboardButton("🗑 Delete Sauce", callback_data="delete_sauce={}".format(file))
        b3 = telebot.types.InlineKeyboardButton("🔙 Go Back", callback_data="cancel={}".format(file))

        sbtn.row(b1, b2)
        sbtn.add(b3)

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=sbtn, custom_caption=True)

    if func == 'edit_link':
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = "What would you like to do?"
        sbtn = telebot.types.InlineKeyboardMarkup(row_width=3)
        b1 = telebot.types.InlineKeyboardButton("📝 Edit Links", callback_data="add_link={}".format(file))
        b2 = telebot.types.InlineKeyboardButton("🗑 Delete Links", callback_data="delete_link={}".format(file))
        b3 = telebot.types.InlineKeyboardButton("🔙 Go Back", callback_data="cancel={}".format(file))

        sbtn.row(b1, b2)
        sbtn.add(b3)

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=sbtn, custom_caption=True)

    if func == 'delete_post':
        buttons = telebot.types.InlineKeyboardMarkup(row_width=3)

        yes_button = telebot.types.InlineKeyboardButton(text="✔️ Yes",
                                                        callback_data="delete_yes={} "
                                                                      "{}".format(file, call.message.message_id))
        no_button = telebot.types.InlineKeyboardButton(text="✖️ No",
                                                       callback_data="cancel={}".format(file))

        buttons.row(yes_button, no_button)
        text = "Are you really sure you want to delete this post?"
        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=buttons, custom_caption=True)

    if func == 'delete_yes':
        mid = call.data.split()[1]

        del gl.create_post[cid].posts[file]
        analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'discarded_posts': 1}})

        text = "Done, post deleted. You can continue sending messages now."
        bot.answer_callback_query(call.id, text)
        bot.delete_message(cid, mid)

    if func == 'sauce_yes':
        post = [gl.create_post[cid].posts[file]]

        preview_posts(bot, gl, call.message, post, update_message=True)
        gl.create_post[cid].queue = True
        del gl.create_post[cid].waiting_post
        bot.answer_callback_query(call.id, "Done! Sauce added.")

    if func == 'sauce_no':
        gl.create_post[cid].queue = 'waiting_sauce'
        gl.create_post[cid].waiting_post = file
        text = 'All right, let\'s redo it. Remember, the sauces are:\n\n' \
               'Pixiv, Gelbooru, Danbooru, Safebooru, Sankaku, Konachan, Yandere\n\n' \
               'To send, use:\n' \
               'Sauce - id/Link'
        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'sauce_cancel' or func == 'delete_sauce':
        del gl.create_post[cid].posts[file].sauce

        if func == 'delete_sauce':
            text = 'Sauce deleted. You can keep sending messages now.'
        else:
            text = "Operation canceled. You can keep sending messages now."
        t = gl.create_post[cid].posts[file]

        # bot.send_message(cid, text, parse_mode='markdown')
        bot.answer_callback_query(call.id, text)
        preview_posts(bot, gl, call.message, file=[t], update_message=True)

        gl.create_post[cid].queue = True
        del gl.create_post[cid].waiting_post

    if func == 'link_yes':
        if 'temp_link_buttons' in gl.create_post[cid].posts[file]:
            gl.create_post[cid].posts[file].link_buttons = gl.create_post[cid].posts[file].temp_link_buttons
            gl.create_post[cid].posts[file].row_width = gl.create_post[cid].posts[file].temp_row_width
        post = gl.create_post[cid].posts[file]

        preview_posts(bot=bot, globs=gl, m=call.message, file=[post], update_message=True)
        gl.create_post[cid].queue = True
        del gl.create_post[cid].waiting_post
        bot.answer_callback_query(call.id, "Done! Links added.")

    if func == 'link_no':
        gl.create_post[cid].queue = 'waiting_buttons_row'
        gl.create_post[cid].waiting_post = file
        text = 'Send your links in the following format:\n\n' \
               '`Name 1 - link1`\n`Name 2 - link2`'
        post = gl.create_post[cid].posts[file]

        preview_posts(bot, gl, call.message, file=[post],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'link_cancel' or func == 'delete_link':
        if func == 'delete_link':

            del gl.create_post[cid].posts[file].link_buttons
            if 'temp_link_buttons' in gl.create_post[cid].posts[file]:
                del gl.create_post[cid].posts[file].temp_link_buttons

        else:
            if 'temp_link_buttons' in gl.create_post[cid].posts[file]:
                del gl.create_post[cid].posts[file].temp_link_buttons
            else:
                del gl.create_post[cid].posts[file].link_buttons
        if func == 'delete_link':
            text = 'Link buttons deleted. You can keep sending messages now.'
        else:
            text = "Operation canceled. You can keep sending messages now."
        t = gl.create_post[cid].posts[file]

        # bot.send_message(cid, text, parse_mode='markdown')
        bot.answer_callback_query(call.id, text)
        preview_posts(bot, gl, call.message, file=[t], update_message=True)

        gl.create_post[cid].queue = True
        del gl.create_post[cid].waiting_post

    if func == 'add_reactions':
        gl.create_post[cid].queue = 'waiting_reactions_row'
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = 'Send me up to 4 emojis for the reactions without spacing or any kind of separation, like the ' \
               'format below:\n\n' \
               '👌😊😔😡'

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'edit_reactions':
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = "What would you like to do?"
        sbtn = telebot.types.InlineKeyboardMarkup(row_width=3)
        b1 = telebot.types.InlineKeyboardButton("📝 Edit Reactions", callback_data="add_reactions={}".format(file))
        b2 = telebot.types.InlineKeyboardButton("🗑 Delete Reactions",
                                                callback_data="delete_reactions={}".format(file))
        b3 = telebot.types.InlineKeyboardButton("🔙 Go Back", callback_data="cancel={}".format(file))

        sbtn.row(b1, b2)
        sbtn.add(b3)

        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=sbtn, custom_caption=True)

    if func == 'reactions_yes':
        post = [gl.create_post[cid].posts[file]]
        gl.create_post[cid].posts[file].custom_reactions = \
            gl.create_post[cid].posts[file].custom_reactions['temp']

        preview_posts(bot, gl, call.message, post, update_message=True)

        gl.create_post[cid].queue = True
        del gl.create_post[cid].waiting_post
        if 'temp' in gl.create_post[cid].posts[file].custom_reactions:
            del gl.create_post[cid].posts[file].custom_reactions['temp']
        bot.answer_callback_query(call.id, "Done! Reactions added.")

    if func == 'reactions_no':
        gl.create_post[cid].queue = 'waiting_reactions_row'
        gl.create_post[cid].waiting_post = file
        gl.create_post[cid].last_msg = call.message.message_id
        text = 'All right, let\'s redo it. Remember, send me up to 4 emojis for the reactions without ' \
               'spacing or any kind of separation, like the format below:\n\n' \
               '👌😊😔😡'
        preview_posts(bot, gl, call.message, file=[gl.create_post[cid].posts[file]],
                      update_message=True, caption=text, buttons=cancel, custom_caption=True)

    if func == 'reactions_cancel' or func == 'delete_reactions':
        if func == 'delete_reactions':
            gl.create_post[cid].posts[file].custom_reactions = None
        else:
            if 'temp' in gl.create_post[cid].posts[file].custom_reactions:
                del gl.create_post[cid].posts[file].custom_reactions['temp']

        if func == 'delete_reactions':
            text = 'Reactions deleted. You can keep sending messages now.'
        else:
            text = "Operation canceled. You can keep sending messages now."
        t = gl.create_post[cid].posts[file]

        # bot.send_message(cid, text, parse_mode='markdown')
        bot.answer_callback_query(call.id, text)
        preview_posts(bot, gl, call.message, file=[t], update_message=True)

        gl.create_post[cid].queue = True
        del gl.create_post[cid].waiting_post

    if func == 'cancel':
        gl.create_post[cid].queue = True
        if 'waiting_post' in gl.create_post[cid]:
            del gl.create_post[cid].waiting_post

        if 'last_msg' in gl.create_post[cid]:
            del gl.create_post[cid].last_msg

        text = "Operation canceled. You can keep sending messages now."
        bot.answer_callback_query(call.id, text)
        preview_posts(bot, gl, call.message, [gl.create_post[cid].posts[file]], update_message=True)
