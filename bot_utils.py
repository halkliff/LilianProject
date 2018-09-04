import telebot
import re
import time


def preview_posts(bot, globs, m, file=None, full_post=False, buttons=None, update_message=False,
                  caption=None, custom_caption=False, preview_only=False):
    cid = m.chat.id
    posts = []

    if file is not None:
        posts = file
    elif full_post is True:
        posts = globs.create_post[cid].posts
    for post in posts:
        if full_post is True:
            post = posts[post]

        if not update_message:
            if post.type == 'photo':
                bot.send_chat_action(cid, 'upload_photo')
            elif post.type == 'text':
                bot.send_chat_action(cid, 'typing')
            elif post.type == 'video':
                bot.send_chat_action(cid, 'upload_video')
            elif post.type == 'document':
                bot.send_chat_action(cid, 'upload_document')

        kb_buttons = telebot.types.InlineKeyboardMarkup(row_width=4) if buttons is None else buttons

        string = post.string

        if not custom_caption:
            caption = post.caption if 'caption' in post else None
            if globs.create_post[cid].default_caption is not None:
                if caption is not None:
                    caption = '{0}\n\n{1}'.format(caption, globs.create_post[cid].default_caption)
                else:
                    caption = globs.create_post[cid].default_caption

        if post.disable_notif is False:
            no_sound_button = telebot.types.InlineKeyboardButton('🔔', callback_data='off_notif={}'.format(string))
        elif globs.create_post[cid].default_silenced:
            no_sound_button = None
        else:
            no_sound_button = telebot.types.InlineKeyboardButton('🔕', callback_data='on_notif={}'.format(string))

        add_sauce_button = telebot.types.InlineKeyboardButton('📎 Add Sauce',
                                                              callback_data='add_sauce={}'.format(string))
        edit_sauce_button = telebot.types.InlineKeyboardButton('✏️ Edit Sauce',
                                                               callback_data='edit_sauce={}'.format(string))

        add_link_button = telebot.types.InlineKeyboardButton('📎 Add Link',
                                                             callback_data='add_link={}'.format(string))
        edit_link_button = telebot.types.InlineKeyboardButton('✏️ Edit Links',
                                                              callback_data='edit_link={}'.format(string))

        add_reactions_button = telebot.types.InlineKeyboardButton("😂 Add Reactions",
                                                                  callback_data='add_reactions={}'.format(string))
        edit_reactions_button = telebot.types.InlineKeyboardButton("🤔 Edit Reactions",
                                                                   callback_data='edit_reactions={}'.format(string))

        edit_text = telebot.types.InlineKeyboardButton('📝 Edit Text',
                                                       callback_data='edit_text={}'.format(string))
        edit_caption = telebot.types.InlineKeyboardButton('📝 Edit Caption',
                                                          callback_data='edit_caption={}'.format(string))

        delete_post = telebot.types.InlineKeyboardButton('🗑', callback_data='delete_post={}'.format(string))
        reactions_buttons = None
        if post.custom_reactions is not None:
            if post.custom_reactions['preview'] is not None:
                reactions_buttons = post.custom_reactions['preview']
            else:
                if globs.create_post[cid].reactions is not None:

                    reactions_buttons = [
                        telebot.types.InlineKeyboardButton(i, callback_data="preview_reaction={}".format(i))
                        for i in globs.create_post[cid].reactions]
        if buttons is None:
            if preview_only:
                if reactions_buttons is not None:
                    kb_buttons.row(*reactions_buttons)

                if 'sauce' in post:
                    sauce_btn = telebot.types.InlineKeyboardButton(post.sauce['label_text'], url=post.sauce['url'])
                    kb_buttons.add(sauce_btn)

                if 'link_buttons' in post:
                    row_width = post['row_width']
                    btns = []
                    for button in post['link_buttons']:
                        link_btn = telebot.types.InlineKeyboardButton(button['label_text'], url=button['url'])
                        btns.append(link_btn)
                    if row_width == 1:
                        for button in btns:
                            kb_buttons.add(button)

                    else:
                        row = [btns[i: i + int(row_width)] for i in range(0, len(btns), int(row_width))]
                        for i in row:
                            kb_buttons.row(*i)
                back_editing = telebot.types.InlineKeyboardButton("🔙 Continue Editing",
                                                                  callback_data='back_editing=%s' % string)
                kb_buttons.add(back_editing)

            else:
                preview_button = telebot.types.InlineKeyboardButton("👁 Preview Post",
                                                                    callback_data='preview_post=%s' % string)
                kb_buttons.add(preview_button)

                if post.type == 'photo' or post.type == 'document' or post.type == 'video':
                    kb_buttons.row(no_sound_button, edit_caption)
                    if 'link_buttons' in post and 'sauce' in post:
                        kb_buttons.row(edit_sauce_button, edit_link_button)
                    elif 'link_buttons' in post and 'sauce' not in post:
                        kb_buttons.row(add_sauce_button, edit_link_button)
                    elif 'sauce' in post and 'link_buttons' not in post:
                        kb_buttons.row(edit_sauce_button, add_link_button)
                    else:
                        kb_buttons.row(add_sauce_button, add_link_button)

                else:
                    kb_buttons.row(no_sound_button, edit_text)
                    if 'link_buttons' in post:
                        kb_buttons.add(edit_link_button)
                    else:
                        kb_buttons.add(add_link_button)
                if reactions_buttons is not None:
                    kb_buttons.add(edit_reactions_button)

                else:
                    kb_buttons.add(add_reactions_button)
                kb_buttons.add(delete_post)

        text = caption if custom_caption else caption if 'caption' in post else post.text

        render_post(bot, m, post, kb_buttons, text, update_message)
        time.sleep(0.5)


def send_posts(bot, posts_dict, data, reactions, disable_web_page_preview=False, disable_notif=False):
    kb = telebot.types.InlineKeyboardMarkup(row_width=5)
    channel = data['channel']
    del posts_dict
    if reactions is not None:
        kb.add(*reactions)

    if 'sauce' in data:
        sauce_link = data['sauce']['label_text']
        sauce_url = data['sauce']['url']
        btn = telebot.types.InlineKeyboardButton(sauce_link, url=sauce_url)
        kb.add(btn)

    if 'link_buttons' in data:
        row_width = data['row_width']
        btns = []
        for button in data['link_buttons']:
            bt = telebot.types.InlineKeyboardButton(button['label_text'], url=button['url'])
            btns.append(bt)
        if row_width == 1:
            for button in btns:
                kb.add(button)

        else:
            row = [btns[i: i + int(row_width)] for i in range(0, len(btns), int(row_width))]
            for i in row:
                kb.row(*i)

    method = None

    caption = data['caption'] if 'caption' in data else None

    if data['type'] == 'photo':
        file_id = data['file_id']

        method = bot.send_photo(channel, file_id, caption=caption, reply_markup=kb,
                                disable_notification=disable_notif)

    if data['type'] == 'text':
        text = data['text']
        method = bot.send_message(channel, text, parse_mode='markdown', reply_markup=kb,
                                  disable_notification=disable_notif, disable_web_page_preview=disable_web_page_preview)

    if data['type'] == 'document':
        doc = data['file_id']

        method = bot.send_document(channel, doc, caption=caption, reply_markup=kb, disable_notification=disable_notif)

    if data['type'] == 'video':
        file_id = data['file_id']
        duration = data['duration']

        method = bot.send_video(channel, file_id, duration=duration,
                                caption=caption, reply_markup=kb, disable_notification=disable_notif,
                                supports_streaming=True)
    return method.wait().message_id


def make_sauce(caption, post, from_text=False):
    no_source = False
    source = caption
    if "--" in caption:
        source = caption.split('--')[1]

    elif "—" in caption:
        source = caption.split('—')[1]

    text = source.replace(" ", "").replace('\n', '')
    if "-" in text:
        breakpoint = text.split("-")
    else:
        raise AttributeError

    if breakpoint is not None:
        source_name = breakpoint[0] if breakpoint is not None else None

        case_test = r'([h-t]+:\/\/+[\w\.\/?=&]+)|([\w.\/]+)(\.[\w\/?=&]+)'
        # link = breakpoint[1] if breakpoint[1].startswith(("http", "https", "www")) else None
        link = breakpoint[1] if re.search(case_test, breakpoint[1]) else False
        source_id = breakpoint[1] if breakpoint[1].isdigit() else False

        if 'pixiv' in source_name.lower():
            if source_id:
                link = 'https://pixiv.net/i/{}'.format(source_id)

        elif 'gelbooru' in source_name.lower():
            if source_id:
                link = 'https://gelbooru.com/index.php?page=post&s=view&id={}'.format(source_id)

        elif 'danbooru' in source_name.lower():
            if source_id:
                link = 'http://danbooru.donmai.us/posts/{}'.format(source_id)

        elif 'safebooru' in source_name.lower():
            if source_id:
                link = 'https://safebooru.org/index.php?page=post&s=view&id={}'.format(source_id)

        elif 'konachan' in source_name.lower():
            if source_id:
                link = 'http://konachan.com/post/show/{}'.format(source_id)

        elif 'yandere' in source_name.lower():
            if source_id:
                link = 'https://yande.re/post/show/{}'.format(source_id)

        elif 'sankaku' in source_name.lower():
            if source_id:
                link = 'https://chan.sankakucomplex.com/post/show/{}'.format(source_id)

        else:
            if not link:
                no_source = True

        if not no_source:
            caption = caption.replace("--", "").replace(source, "").replace("—", "").\
                replace(" -- ", "").replace(source, "").replace(" — ", "").replace("\n--\n", "").\
                replace(source, "").replace("\n—\n", "")
            post.sauce = {'label_text': "Source: [{}]".format(source_name.title()), 'url': link}
            if not from_text:
                post.caption = caption


def fetch_tags(cid, gl, txt, post_id):
    if txt is not None:
        if isinstance(txt, str):
            tags = re.findall("(#\w+)", txt)

            gl.create_post[cid].posts[post_id].tags = gl.create_post[cid].main_tags + tags
            return gl.create_post[cid].posts[post_id].tags


def render_post(bot, m, file=None, kb=None, text=None, update_message=None):
    """This Function Renders post messages, for preview in posts, drafts, queued posts and User File Viewing"""
    cid = m.chat.id
    if kb is None:
        kb = telebot.types.InlineKeyboardMarkup(row_width=4)
        reactions_buttons = [telebot.types.InlineKeyboardButton(i,
                                                                callback_data="preview_reaction={}".format(i)) for i in
                             file['custom_reactions']['reactions']]

        if reactions_buttons is not None:
            kb.row(*reactions_buttons)

        if 'sauce' in file:
            sauce_btn = telebot.types.InlineKeyboardButton(file['sauce']['label_text'], url=file['sauce']['url'])
            kb.add(sauce_btn)

        if 'link_buttons' in file:
            row_width = file['row_width']
            btns = []
            for button in file['link_buttons']:
                link_btn = telebot.types.InlineKeyboardButton(button['label_text'], url=button['url'])
                btns.append(link_btn)
            if row_width == 1:
                for button in btns:
                    kb.add(button)
            else:
                row = [btns[i: i + int(row_width)] for i in range(0, len(btns), int(row_width))]
                for i in row:
                    kb.row(*i)

    if file['type'] == 'photo':
        text = file['caption'] if text is None else text
        if update_message:
            bot.edit_message_caption(caption=text, chat_id=cid, message_id=m.message_id, reply_markup=kb)
        else:
            bot.send_photo(cid, file['file_id'], caption=text, reply_markup=kb)

    elif file['type'] == 'text':
        text = file['text'] if text is None else text
        if update_message:
            bot.edit_message_text(text, cid, m.message_id, parse_mode='markdown', reply_markup=kb)
        else:
            bot.send_message(cid, text, parse_mode='markdown', reply_markup=kb)

    elif file['type'] == 'document':
        text = file['caption'] if text is None else text
        if update_message:
            bot.edit_message_caption(text, cid, m.message_id, reply_markup=kb)
        else:
            bot.send_document(cid, file['file_id'], caption=text, reply_markup=kb)

    elif file['type'] == 'video':
        text = file['caption'] if text is None else text
        if update_message:
            bot.edit_message_caption(text, cid, m.message_id, reply_markup=kb)
        else:
            bot.send_video(cid, file['file_id'], duration=file['duration'],
                           caption=text, reply_markup=kb)


def message_user(bot, m, gl,  data, user_to_send, members):
    """
    :param bot:
    :param m:
    :param gl:
    :param data: Data must be in the following format: {'type': None
                                                        'caption': None,
                                                        'text': None,
                                                        'file_id': None}
    :param user_to_send:
    :param members:
    :return:

    """
    import datetime
    import time
    import components

    member = members.get({'user_id': user_to_send})

    if member is None:
        return bot.send_message(m.chat.id, 'Couldn\'t send message to user {}. Not registered.'.format(user_to_send))

    saving_data = {'message_from': {'name': m.from_user.first_name,
                                    'username': m.from_user.username,
                                    'id': m.from_user.id},
                   'data': {'type': data['type'],
                            'caption': data['caption'],
                            'text': data['text'],
                            'file_id': data['file_id'],
                            'title': data['title']},
                   'date': time.mktime(datetime.datetime.utcnow().timetuple()),
                   'read': False
                   }

    members.update({'user_id': user_to_send}, {'$addToSet': {'inbox': saving_data}})
    flag = False
    if 'edit_channel_info' in gl:
        if user_to_send in gl.edit_channel_info:
            flag = True
    if 'add_channel' in gl:
        if user_to_send in gl.add_channel:
            flag = True
    if 'create_post' in gl:
        if user_to_send in gl.create_post:
            flag = True

    if flag:
        return

    txt = 'You have a new inbox message.'
    kb = components.callback_kbbuttons.main_menu_admin(user_to_send)

    return bot.send_message(chat_id=user_to_send, text=txt, reply_markup=kb, parse_mode='markdown')


def render_message(bot, m, user, data, update_message=False, kb=None):
    """'data': {'type': data['type'],
                            'caption': data['caption'],
                            'text': data['text'],
                            'file_id': data['file_id']},"""

    if data['type'] == 'photo':
        if update_message:
            m = bot.edit_message_caption(caption=data['caption'],
                                         chat_id=user, message_id=m.message_id, reply_markup=kb)
        else:
            m = bot.send_photo(user, data['file_id'], caption=data['caption'], reply_markup=kb)
    elif data['type'] == 'text':
        if update_message:
            m = bot.edit_message_text(data['text'], user, m.message_id, parse_mode='markdown', reply_markup=kb)
        else:
            m = bot.send_message(user, data['text'], parse_mode='markdown', reply_markup=kb)
    elif data['type'] == 'document':
        if update_message:
            m = bot.edit_message_caption(data['caption'], user, m.message_id, reply_markup=kb)
        else:
            m = bot.send_document(user, data['file_id'], caption=data['caption'], reply_markup=kb)
    elif data['type'] == 'video':
        if update_message:
            m = bot.edit_message_caption(data['caption'], user, m.message_id, reply_markup=kb)
        else:
            m = bot.send_video(user, data['file_id'], caption=data['caption'], reply_markup=kb)

    return m.wait()
