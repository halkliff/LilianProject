import telebot
import datetime
import time
from Main import analytics_main
import config
from utils import async, Dictionary


class Reactions:
    from Main import bot, reactions
    bot = bot
    reactions = reactions
    cache = Dictionary({})

    def __init__(self, name=""):
        self.name = name

    def add(self, channel, file_id, message_id, sauce=None, links=None, row_width=None):
        if channel not in self.cache:
            self.cache[channel] = Dictionary({'last_update': time.time(),
                                              'files': Dictionary({}),
                                              'paused': False,
                                              'delayed': False})

            self._channel_worker(channel)

        while self.cache[channel].paused:
            pass
        tr = Dictionary({'file_id': file_id,
                         'message_id': message_id,
                         'sauce_btn': sauce,
                         'link_btns': links,
                         'row_width': row_width})
        if file_id not in self.cache[channel].files:
            self.cache[channel].files[file_id] = tr
        else:
            self.cache[channel].files.pop(file_id)
            self.cache[channel].files[file_id] = tr
        return file_id in self.cache[channel].files

    def is_delayed(self, channel_id):
        return channel_id in self.cache and self.cache[channel_id].delayed

    @async()
    def _channel_worker(self, channel_id):
        if channel_id in self.cache:
            while not self.cache[channel_id].files:
                # await a new reaction to be made
                pass
            max_tries = 0
            while max_tries < 3:
                self.cache[channel_id].paused = True
                if not self.cache[channel_id].files:
                    max_tries += 1
                    self.cache[channel_id].paused = False
                    self.cache[channel_id].delayed = False
                    time.sleep(2)
                    continue

                item = self.cache[channel_id].files.pop(list(self.cache[channel_id].files.keys())[0])
                kb = telebot.types.InlineKeyboardMarkup(row_width=5)
                rcts = self.reactions.get({'id': item.file_id})

                reactions_buttons = []
                for rct_code in rcts['reactions']:
                    cb_data = "reaction={0}&{1}".format(item.file_id, rct_code)
                    btn = telebot.types.InlineKeyboardButton(text="%s %s" % (rcts['reactions'][rct_code]['em'],
                                                                             rcts['reactions'][rct_code]['count']),
                                                             callback_data=cb_data)
                    reactions_buttons.append(btn)

                kb.add(*reactions_buttons)

                if item.sauce_btn is not None:
                    kb.add(item.sauce_btn)

                if item.link_btns is not None:
                    row_width = item.row_width if item.row_width else 1

                    row = [item.link_btns[i: i + int(row_width)] for i in range(0, len(item.link_btns), int(row_width))]
                    for i in row:
                        kb.row(*i)

                try:
                    self.bot.edit_message_reply_markup(channel_id, item.message_id, reply_markup=kb)
                except:
                    pass

                self.cache[channel_id].delayed = True
                self.cache[channel_id].paused = False
                self.cache[channel_id].last_update = time.time()
                max_tries = 0
                time.sleep(4.5)
            self.cache.pop(channel_id)
            return
        return


reaction_workers = Reactions(name="REACTIONS WORKERS")


def reactions_handler(bot, call, files, reactions, reactions_cache, logger):
    if call.message:
        chid = call.message.chat.id
        cid = call.from_user.id
        try:
            mid = call.message.message_id
            splt = call.data.split('&')
            file_code = splt[0].split('=')[1]
            reaction_code = splt[1]

            btns = telebot.types.InlineKeyboardMarkup(row_width=5)

            cache = reactions_cache.read(file_code)

            rcts = reactions.get({'id': file_code})

            today = time.mktime(datetime.datetime.utcnow().timetuple())
            if cache is None:
                cache = {}
                file = files.get({'id': file_code})
                if file is None:
                    bot.answer_callback_query(call.id, 'Sorry! But this file is no longer available.',
                                              show_alert=True)
                    return bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                         message_id=call.message.message_id,
                                                         inline_message_id=call.id,
                                                         reply_markup=None)
                if 'link_buttons' in file:
                    cache.update({'link_buttons': file['link_buttons'], 'row_width': file['row_width']})

                if 'sauce' in file:
                    cache.update({'sauce': file['sauce']})

            if rcts is None:
                if 'sauce' in cache:
                    if cache['sauce'] is not None:
                        sauce_btn = telebot.types.InlineKeyboardButton(cache['sauce']['label_text'],
                                                                       url=cache['sauce']['url'])
                        btns.add(sauce_btn)

                if 'link_buttons' in cache:
                    if cache['link_buttons'] is not None:
                        row_width = cache['row_width']
                        bts = []
                        for button in cache['link_buttons']:
                            bt = telebot.types.InlineKeyboardButton(button['label_text'], url=button['url'])
                            bts.append(bt)
                        row = [btns[i: i + int(row_width)] for i in range(0, len(bts), int(row_width))]
                        for i in row:
                            btns.row(*i)
                return bot.edit_message_reply_markup(chid, mid, call.id, reply_markup=btns)

            if str(cid) in rcts['reaction_list']:
                rcache_code = rcts['reaction_list'][str(cid)]['reaction_code']
                if rcache_code == reaction_code:
                    message = "You don't %s it anymore." % rcts['reactions'][reaction_code]['em']
                    rcts['reactions'][reaction_code]['count'] -= 1
                    analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'overall_reactions': -1}})
                    del rcts['reaction_list'][str(cid)]

                else:
                    message = "You %s it." % rcts['reactions'][reaction_code]['em']
                    rcts['reactions'][rcache_code]['count'] -= 1
                    rcts['reactions'][reaction_code]['count'] += 1
                    rcts['reaction_list'][str(cid)] = {"user_id": cid,
                                                       "reaction_code": reaction_code,
                                                       "date": today
                                                       }
            else:
                message = "You %s it." % rcts['reactions'][reaction_code]['em']
                rcts['reactions'][reaction_code]['count'] += 1
                rcts['reaction_list'][str(cid)] = {"user_id": cid,
                                                   "reaction_code": reaction_code,
                                                   "date": today
                                                   }
                analytics_main.update({'_id': config.ANALYTICS_MAIN}, {'$inc': {'overall_reactions': 1}})

            sauce_btn = None
            if 'sauce' in cache:
                if cache['sauce'] is not None:
                    sauce_btn = telebot.types.InlineKeyboardButton(cache['sauce']['label_text'],
                                                                   url=cache['sauce']['url'])
            link_btns = []
            row_width = None
            if 'link_buttons' in cache:
                if cache['link_buttons'] is not None:
                    row_width = cache['row_width']
                    for button in cache['link_buttons']:
                        bt = telebot.types.InlineKeyboardButton(button['label_text'], url=button['url'])
                        link_btns.append(bt)
            try:
                reactions.update({'id': file_code}, {'$set': {'reaction_list': rcts['reaction_list'],
                                                              'reactions': rcts['reactions']}})

                reactions_cache.update(file_code, cache, 4 * 60 * 60)
                reaction_workers.add(chid, file_code, call.message.message_id, sauce_btn, link_btns, row_width)
                if reaction_workers.is_delayed(chid):
                    return bot.answer_callback_query(call.id,
                                                     message + "\n\nCounters in the post will be updated soon.",
                                                     show_alert=True)
                return bot.answer_callback_query(call.id, message)
            except Exception as e:
                message = "An Error has occurred. Please, try again."
                bot.answer_callback_query(call.id, message)
                raise e
        except Exception as e:
            import traceback
            from Main import GLOBAL, bot
            import utils
            cid = call.message.chat.id
            report = "User {0} ({1}) Reported the following issue:\n\n" \
                     "{2}\n\n{3}\n\n" \
                     "REPORT CODE: {4}\n\nMSG:{5}".format(cid, call.from_user.first_name, str(e),
                                                          str(traceback.format_exc()), 'REACTION:',
                                                          'call_data: %s' % str(call.data))
            bot.send_message(123956344, report)
            logger.error("Error occurred: %s\n%s" % (e, str(traceback.format_exc())))
