import telebot
import datetime
from Main import members, logger, GLOBAL
import utils
#import sys


@utils.owner_access(log=logger, db=members)
def my_inbox(bot, m):
    cid = m.chat.id
    member = members.get({'user_id': cid})
    bt_lst = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']
    kb = telebot.types.InlineKeyboardMarkup(row_width=4)
    t = member['inbox'][::-1]

    if len(t) < 1:
        txt = 'You do not have any Messages yet.'

    else:
        txt = 'Here you are, your Messages.\n\n'
        if len(t) > 8:
            ct = 8
        else:
            ct = len(t)
        btns = []
        text_list = []
        for i in range(ct):
            btn = telebot.types.InlineKeyboardButton(bt_lst[i],
                                                     callback_data="my_inbox=view view=%d nav=0" % i)
            btns.append(btn)
            prep = '%(p_id)s _%(date)s_ | *%(from_user)s*: _%(title)s_' % {
                   'p_id': bt_lst[i],
                   'date': datetime.date.fromtimestamp(int(t[i]['date'])).strftime("%b %d"),
                   'from_user': t[i]['message_from']['name'],
                   'title': t[i]['data'].get('title', 'No Title')
                }
            text_list.append(prep)

        kb.add(*btns)

        txt += '\n'.join(text_list)

        if ct == 8:  # Have more than 8 queued posts
            next_button = telebot.types.InlineKeyboardButton("▶️",
                                                             callback_data="my_inbox=navigate nav=1")
            kb.add(next_button)
    return bot.send_message(chat_id=cid, text=txt, parse_mode='markdown', reply_markup=kb)

working = []


def my_inbox_handler(bot, call):
    split_data = call.data.split()
    cid = call.message.chat.id
    if cid in working:
        while cid in working:
            pass
    try:
        from bot_utils import render_message
        from components.callback_kbbuttons import main_menu_admin
        arg = split_data[0].split('=')[1]
        member = members.get({'user_id': cid})
        bt_lst = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']
        kb = telebot.types.InlineKeyboardMarkup(row_width=4)
        if arg == 'navigate':
            n = int(split_data[1].split('=')[1])
            btns = []

            inbox = member['inbox'][::-1]
            inbox_messages = inbox
            aut_num = 8 * n
            auth = inbox[aut_num:]
            if len(inbox_messages) < 1:
                txt = 'You do not have any Messages yet.'

            else:
                txt = 'Here you are, your Messages.\n\n'

            if len(auth) > 8:
                ct = 8
            else:
                ct = len(auth)
            text_list = []
            for i in range(ct):
                btn = telebot.types.InlineKeyboardButton(bt_lst[i],
                                                         callback_data="my_inbox=view view=%d nav=%d" % ((aut_num + i),
                                                                                                         i))

                prep = '%(p_id)s _%(date)s_ | *%(from_user)s*: _%(title)s_' % {
                    'p_id': bt_lst[i],
                    'date': datetime.date.fromtimestamp(int(auth[i]['date'])).strftime("%b %d"),
                    'from_user': auth[i]['message_from']['name'],
                    'title': auth[i]['data'].get('title', 'No Title')
                }
                text_list.append(prep)
                btns.append(btn)

            txt += '\n'.join(text_list)

            next_button = telebot.types.InlineKeyboardButton("▶️",
                                                             callback_data="my_posts=navigate "
                                                                           "%s=%s" % (type, n + 1))
            previous_button = telebot.types.InlineKeyboardButton("◀️",
                                                                 callback_data="my_posts=navigate "
                                                                               "%s=%s" % (type, n - 1))

            kb.add(*btns)
            if n == 0 and len(inbox_messages) <= 8:
                pass

            else:
                if len(inbox_messages) <= 8 * (n + 1):
                    kb.add(previous_button)

                elif len(inbox_messages) > (8 * (n + 1)) and n - 1 >= 0:
                    kb.add(previous_button, next_button)

                else:
                    kb.add(next_button)
            # return bot.edit_message_reply_markup(cid, call.message.message_id, call.id, reply_markup=kb)

            return bot.edit_message_text(txt, cid, call.message.message_id, call.id,
                                         reply_markup=kb, parse_mode='markdown')

        elif arg == 'view':
            working.append(cid)
            view_id = int(split_data[1].split('=')[1])
            n = int(split_data[2].split('=')[1])

            messages = members.get({'user_id': cid})['inbox'][::-1]
            message = messages[view_id]
            if not message['read']:
                message['read'] = True
                members.update({'user_id': cid}, {'$set': {'inbox': messages[::-1]}})
            back = telebot.types.InlineKeyboardButton("🔙",
                                                      callback_data="my_inbox=back view_id=%d nav=%d" % (view_id, n))
            delete = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                        callback_data='my_inbox=delete '
                                                                      'del=%d y=0 nav=%d' % (view_id, n))
            kb.add(back, delete)
            kyb = main_menu_admin(cid)
            bot.send_message(chat_id=cid, text="Here you are your message.", reply_markup=kyb).wait()
            render_message(bot, call.message, cid, message['data'], kb=kb)
            working.remove(cid)

            return bot.delete_message(cid, call.message.message_id)

        elif arg == 'delete':
            """my_inbox=delete del=%d y=0 nav=%d"""

            del_id = int(split_data[1].split('=')[1])
            deleting = split_data[2].split('=')[1]
            n = int(split_data[3].split('=')[1])

            if deleting == 'Yes':
                working.append(cid)
                member_messages = members.get({'user_id': cid})['inbox'][::-1]
                member_messages.pop(del_id)
                members.update({'user_id': cid}, {'$set': {'inbox': member_messages[::-1]}})
                bot.answer_callback_query(call.id, "Done. Message deleted.")
                bot.delete_message(cid, call.message.message_id)
                call.data = "my_inbox=navigate nav=%d" % n
                mid = bot.send_message(cid, '.').wait().message_id
                call.message.message_id = mid
                working.remove(cid)
                return my_inbox_handler(bot, call)
            elif deleting == 'No':
                call.data = "my_inbox=navigate nav=%d" % n

                view_id = int(split_data[1].split('=')[1])
                n = int(split_data[3].split('=')[1])
                messages = members.get({'user_id': cid})['inbox'][::-1]
                message = messages[view_id]

                back = telebot.types.InlineKeyboardButton("🔙",
                                                          callback_data="my_inbox=back "
                                                                        "view_id=%d nav=%d" % (view_id, n))
                delete = telebot.types.InlineKeyboardButton("🗑 Delete",
                                                            callback_data='my_inbox=delete '
                                                                          'del=%d y=0 nav=%d' % (view_id, n))
                kb.add(back, delete)

                render_message(bot, call.message, cid, message['data'], update_message=True, kb=kb)

                return my_inbox_handler(bot, call)
            else:
                txt = 'Are you sure you want to delete this message? This action can not be undone.'
                yes_btn = telebot.types.InlineKeyboardButton("Yes",
                                                             callback_data='my_inbox=delete '
                                                                           'del=%d y=Yes nav=%d' % (del_id, n))
                no_btn = telebot.types.InlineKeyboardButton("No",
                                                            callback_data='my_inbox=delete '
                                                                          'del=%d y=No nav=%d' % (del_id, n))
                kb.row(yes_btn, no_btn)
                render_message(bot, call.message, cid, {'type': 'text', 'text': txt}, update_message=True, kb=kb)

        elif arg == 'back':
            view_id = int(split_data[1].split('=')[1])
            n = int(split_data[2].split('=')[1])
            messages = members.get({'user_id': cid})['inbox'][::-1]
            message = messages[view_id]
            render_message(bot, call.message, cid, message['data'], update_message=True)
            call.data = 'my_inbox=navigate nav=%d' % n
            return my_inbox_handler(bot, call)
    except Exception as e:
        import traceback
        utils.report_msg(bot, call.message, GLOBAL, e, str(traceback.format_exc()), msg="call_data: " + call.data)
        logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
