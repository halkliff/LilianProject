import telebot
import utils
from utils import admin_access
from Main import logger, deep_link_cache
import Data
# import components
import json
import config

channels = Data.Database(Data.channels_db.channels)


@admin_access(log=logger)
def admin(bot, m):
    kb = telebot.types.InlineKeyboardMarkup(row_width=3)
    kbbtn1 = telebot.types.InlineKeyboardButton("📈 Statistics", callback_data='admin=stats')
    kbbtn2 = telebot.types.InlineKeyboardButton("📝Administrate Channels", callback_data='admin=channels')
    kbbtn3 = telebot.types.InlineKeyboardButton("🌐 New Broadcast", callback_data='admin=broadcast')
    kbbtn4 = telebot.types.InlineKeyboardButton("Message Admins", callback_data='admin=admin_broadcast message=waiting')
    kbbtn5 = telebot.types.InlineKeyboardButton("Add Networkers", callback_data='admin=add_networkers')
    kb.add(kbbtn2)
    kb.row(kbbtn1, kbbtn3)
    kb.add(kbbtn4, kbbtn5)
    bot.reply_to(m, "Select one of the options below:", reply_markup=kb)
    return


@admin_access(log=logger)
def admin_handler(bot, call, gl):
    if call.message:
        cid = call.message.chat.id
        spl_data = call.data.split()

        reason = spl_data[0].split('=')[1]

        kb = telebot.types.InlineKeyboardMarkup(row_width=4)

        if reason == 'stats':
            pass

        if reason == 'channels':
            if len(spl_data) < 2:

                b1 = telebot.types.InlineKeyboardButton("Promote Post",
                                                        callback_data='admin=channels promote_post=True')
                b2 = telebot.types.InlineKeyboardButton("Publish Channels",
                                                        callback_data='admin=channels publish_channels=True')
                b3 = telebot.types.InlineKeyboardButton("Update Channels List",
                                                        callback_data='admin=channels update_ch_list=True')
                kb.row(b1, b2)
                kb.add(b3)
                return bot.edit_message_text("Choose an Option:", cid, call.message.message_id, call.id,
                                             reply_markup=kb)
            else:
                func = spl_data[1].split('=')[0]

                if func == 'publish_channels':

                    arg = spl_data[1].split('=')[1]
                    if arg == 'True':
                        all_channels = channels.search({'channel_tier': {'$ne': None}})
                        bts = []
                        kb = telebot.types.InlineKeyboardMarkup(row_width=2)
                        for i in all_channels:
                            btn = telebot.types.InlineKeyboardButton(i['channel_name'],
                                                                     callback_data='admin=channels '
                                                                                   'publish_channels=%d' %
                                                                                   i['channel_id'])
                            bts.append(btn)

                        kb.add(*bts)
                        back = telebot.types.InlineKeyboardButton("🔙", callback_data='admin=channels')
                        kb.add(back)
                        txt = 'Publish channels by tapping the button'
                        return bot.edit_message_text(txt, chat_id=cid, message_id=call.message.message_id,
                                                     parse_mode='markdown', reply_markup=kb)

                    else:
                        channel = channels.get({'channel_id': int(arg)})
                        if channel['channel_private_link'] is None:
                            if channel['channel_username'] is None:
                                txt = 'Channel {} missing Link'.format(channel['channel_name'])
                                return bot.answer_callback_query(call.id, text=txt, show_alert=True)

                        capt = '📢  %(hch)s%(ch_name)s \n\n🏷  %(desc)s' % {
                            'hch': '👁‍🗨' if channel['channel_id'] in config.CHANNELS else '',
                            'ch_name': channel['channel_name'],
                            'desc': channel['channel_info'][:(191 - len(channel['channel_name']))] if
                            channel['channel_info'] is not None else ''}
                        rating = '(+18)' if '#explicit' in channel['channel_tags'] else '(+16)' if \
                            '#questionable' in channel['channel_tags'] else ''

                        s = bot.send_photo(chat_id=config.PUB_CHANNEL, photo=channel['channel_profile_pic'],
                                           caption=capt, disable_notification=True).wait()

                        if isinstance(s, tuple):
                            print(s)
                            txt = 'Channel {} with Invalid Profile Pic.'.format(channel['channel_name'])
                            show_alert = True

                        else:
                            join_btn = telebot.types.InlineKeyboardButton('Join Now! ' + rating,
                                                                          url=channel['channel_private_link'] if
                                                                          channel[
                                                                              'channel_private_link'] is not None else
                                                                          't.me/' + channel['channel_username'])
                            header = '**Join Now!**'.replace(" ", "%20")
                            text = '\nJoin now __{0}__, an amazing channel!\n\n' \
                                   't.me/HalksPUB/{1}'.format(channel['channel_name'], s.message_id).replace(
                                        "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                                        "\n", "%0A").replace(",", "%2C").replace("=", "%3D").replace("+", "%2B")
                            url = 'https://t.me/share/url?url={0}&text={1}'.format(header, text)
                            share_btn = telebot.types.InlineKeyboardButton("Share with Friends!", url=url)
                            kb.add(share_btn)
                            kb.add(join_btn)
                            bot.edit_message_reply_markup(chat_id=config.PUB_CHANNEL,
                                                          message_id=s.message_id, reply_markup=kb)
                            txt = 'Channel {} Published'.format(channel['channel_name'])
                            show_alert = None
                            channels.update({'channel_id': int(arg)}, {'$set': {'pub_id': s.message_id}})

                        return bot.answer_callback_query(call.id, text=txt, show_alert=show_alert)

                elif func == 'update_ch_list':
                    bot.answer_callback_query(call.id, 'Updating channels...')
                    sfw_channels = channels.search({'channel_tier': 'SFW'})
                    nsfw_channels = channels.search({'channel_tier': 'NSFW'})
                    other_channels = channels.search({'channel_tier': 'OTHER'})
                    other_txt = """\`
                  [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
            _Eastern Media Network_
    
    *Cosplays, Asians & Others*\n\n"""

                    nsfw_txt = """\`
                  [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
            _Eastern Media Network_
    
    *Hentai, Ecchi and kinky anime*\n\n"""

                    sfw_txt = """\`
                  [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
            _Eastern Media Network_
    
    *Anime artworks, news & fanbase:*\n\n"""

                    ot = []
                    for i in other_channels:
                        t = '%(view)s [%(rt)s %(ch_halk)s %(ch_name)s](%(ch_link)s)' % {
                                'ch_halk': '👁‍🗨' if i['channel_id'] in config.CHANNELS else '',
                                'ch_link': i['channel_private_link'] if i['channel_private_link'] is not None else
                                           't.me/' + i['channel_username'],
                                'ch_name': i['channel_name'],
                                'rt': '🔞' if '#explicit' in i['channel_tags'] else '',
                                'view': '[|👁|](t.me/HalksPUB/%s)' % i['pub_id'] if 'pub_id' in i else ''
                            }
                        ot.append(t)
                    other_txt += '\n'.join(ot) + '\n\n📋_Channels with 👁‍🗨 are Hαlk\'s Franchise Channels._\n' \
                                                 'ℹ️ @HalksNET'

                    sf = []
                    for i in sfw_channels:
                        t = '%(view)s [%(ch_halk)s %(ch_name)s](%(ch_link)s)' % {
                                'ch_halk': '👁‍🗨' if i['channel_id'] in config.CHANNELS else '',
                                'ch_link': i['channel_private_link'] if i['channel_private_link'] is not None else
                                't.me/' + i['channel_username'],
                                'ch_name': i['channel_name'],
                                'view': '[|👁|](t.me/HalksPUB/%s)' % i['pub_id'] if 'pub_id' in i else ''
                            }
                        sf.append(t)
                    sfw_txt += '\n'.join(sf) + '\n\n📋_Channels with 👁‍🗨 are Hαlk\'s Franchise Channels._\n' \
                                               'ℹ️ @HalksNET'

                    nsf = []
                    for i in nsfw_channels:
                        t = '%(view)s [%(rt)s %(ch_halk)s %(ch_name)s](%(ch_link)s)' % {
                                'ch_halk': '👁‍🗨' if i['channel_id'] in config.CHANNELS else '',
                                'ch_link': i['channel_private_link'] if i['channel_private_link'] is not None else
                                't.me/' + i['channel_username'],
                                'ch_name': i['channel_name'],
                                'rt': '🔞' if '#explicit' in i['channel_tags'] else '',
                                'view': '[|👁|](t.me/HalksPUB/%s)' % i['pub_id'] if 'pub_id' in i else ''
                            }
                        nsf.append(t)
                    nsfw_txt += '\n'.join(nsf) + '\n\n📋_Channels with 👁‍🗨 are Hαlk\'s Franchise Channels._\n' \
                                                 'ℹ️ @HalksNET'

                    with open('etc/published_list.json', 'r') as r:
                        updt_msg = json.loads(r.read())
                    if updt_msg.get('sfw_mid', None) is None:
                        sfw_mid = bot.send_message(config.HALKSNET_CHANNEL, sfw_txt, parse_mode='markdown').wait()
                    else:
                        sfw_mid = bot.edit_message_text(text=sfw_txt, chat_id=config.HALKSNET_CHANNEL,
                                                        message_id=updt_msg.get('sfw_mid', None),
                                                        parse_mode='markdown').wait()

                    header = '**Take a Look!**'.replace(
                        "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                        "\n", "%0A").replace(",", "%2C").replace("=", "%3D")
                    text = '\nWe have the best anime media right here! Join us, and see our channels!\n\n' \
                           't.me/HalksNET/{0}'.format(updt_msg.get('other_mid')).replace(
                                "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                                "\n", "%0A").replace(",", "%2C").replace("=", "%3D")
                    url = 'https://t.me/share/url?url={0}&text={1}'.format(header, text)
                    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
                    kb.add(telebot.types.InlineKeyboardButton("Share these Channels!", url=url))
                    bot.edit_message_reply_markup(chat_id=config.HALKSNET_CHANNEL,
                                                  message_id=sfw_mid.message_id, reply_markup=kb)

                    if isinstance(sfw_mid, tuple):
                            # 'not updated message'
                            pass
                    else:
                            updt_msg.update({'sfw_mid': sfw_mid.message_id})

                    if updt_msg.get('nsfw_mid', None) is None:
                            nsfw_mid = bot.send_message(config.HALKSNET_CHANNEL, nsfw_txt, parse_mode='markdown').wait()
                    else:
                            nsfw_mid = bot.edit_message_text(text=nsfw_txt, chat_id=config.HALKSNET_CHANNEL,
                                                             message_id=updt_msg.get('nsfw_mid', None),
                                                             parse_mode='markdown').wait()
                    header = '**Take a Look!**'.replace(
                                "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                                "\n", "%0A").replace(",", "%2C").replace("=", "%3D")
                    text = '\nWe have the best anime lewds! Join us, and see our channels!\n\n' \
                           't.me/HalksNET/{0}'.format(updt_msg.get('nsfw_mid')).replace(
                                "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                                "\n", "%0A").replace(",", "%2C").replace("=", "%3D")
                    url = 'https://t.me/share/url?url={0}&text={1}'.format(header, text)
                    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
                    kb.add(telebot.types.InlineKeyboardButton("Share these Channels!", url=url))
                    bot.edit_message_reply_markup(chat_id=config.HALKSNET_CHANNEL,
                                                  message_id=nsfw_mid.message_id, reply_markup=kb)

                    if isinstance(nsfw_mid, tuple):
                            # 'not updated message'
                            pass
                    else:
                            updt_msg.update({'nsfw_mid': nsfw_mid.message_id})

                    if updt_msg.get('other_mid', None) is None:
                        other_mid = bot.send_message(config.HALKSNET_CHANNEL, other_txt,
                                                     parse_mode='markdown').wait()
                    else:
                        other_mid = bot.edit_message_text(text=other_txt, chat_id=config.HALKSNET_CHANNEL,
                                                          message_id=updt_msg.get('other_mid', None),
                                                          parse_mode='markdown').wait()

                    header = '**Take a Look!**'.replace("/", "%2F").replace("?", "%3F").replace(
                        " ", "%20").replace("\n", "%0A").replace(",", "%2C").replace("=", "%3D")
                    text = '\nWe have some good Eastern stuff right here! Join us, and see our channels!\n\n' \
                           't.me/HalksNET/{0}'.format(updt_msg.get('other_mid')).replace(
                                "/", "%2F").replace("?", "%3F").replace(" ", "%20").replace(
                                "\n", "%0A").replace(",", "%2C").replace("=", "%3D")
                    url = 'https://t.me/share/url?url={0}&text={1}'.format(header, text)
                    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
                    kb.add(telebot.types.InlineKeyboardButton("Share these Channels!", url=url))
                    bot.edit_message_reply_markup(chat_id=config.HALKSNET_CHANNEL,
                                                  message_id=other_mid.message_id, reply_markup=kb)

                    if isinstance(other_mid, tuple):
                            # 'not updated message'
                            pass
                    else:
                            updt_msg.update({'other_mid': other_mid.message_id})

                    cover_msg = """\`
                  [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
            _Eastern Media Network_
    
    The best, hand selected Eastern (_Nippon_) based channels.
    
    We have selected channels, for your joy! 
    
    _See our lists_:
    
    [▪️ Anime Artworks, news & fanbase](https://t.me/HalksNET/%(sfw)s)
    [▪️ Hentai, Ecchi & Kinky Anime](https://t.me/HalksNET/%(nsfw)s)
    [▪️ Cosplays, Asians & Others](https://t.me/HalksNET/%(other)s)
    
       _Come join us now! (っ´▽`)っ_""" % {'sfw': updt_msg.get('sfw_mid', None),
                                         'nsfw': updt_msg.get('nsfw_mid', None),
                                         'other': updt_msg.get('other_mid', None)}

                    if updt_msg.get('cover', None) is None:
                            cover = bot.send_message(config.HALKSNET_CHANNEL, cover_msg, parse_mode='markdown').wait()
                    else:
                            cover = bot.edit_message_text(text=cover_msg, chat_id=config.HALKSNET_CHANNEL,
                                                          message_id=updt_msg.get('cover', None),
                                                          parse_mode='markdown').wait()

                    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
                    bt1 = telebot.types.InlineKeyboardButton("See our Publisher!", url='https://t.me/HalksPUB')
                    bt2 = telebot.types.InlineKeyboardButton("Join your Channel!", callback_data='join_channel=True')
                    kb.add(bt2)
                    kb.add(bt1)
                    bot.edit_message_reply_markup(chat_id=config.HALKSNET_CHANNEL,
                                                  message_id=updt_msg.get('cover', None), reply_markup=kb)

                    if isinstance(cover, tuple):
                            # 'not updated message'
                            pass
                    else:
                            updt_msg.update({'cover': cover.message_id})

                    with open('etc/published_list.json', 'w') as r:
                        dump = json.dumps(updt_msg)
                        r.write(dump)

                    return

                elif func == 'promote_post':

                    sfw_channels = channels.search({'channel_tier': 'SFW'})
                    nsfw_channels = channels.search({'channel_tier': 'NSFW'})
                    other_channels = channels.search({'channel_tier': 'OTHER'})
                    other_txt = """\`
              [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
        _Eastern Media Network_

We have the best cosplays, and other 
Eastern media for you!
*Check these out:*\n\n"""

                    nsfw_txt = """\`
              [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
        _Eastern Media Network_

We have the best and most
exciting hentai and ecchi for you!
*Check these out:*\n\n"""

                    sfw_txt = """\`
              [👁‍🗨](t.me/halksnet)_@Hαlks_*NET*
        _Eastern Media Network_

We have the best anime and
Japanese media channels for you! 
*Check these out:*\n\n"""

                    ot = []
                    for i in other_channels:
                        t = '▪️ [%(rt)s %(ch_name)s](%(ch_link)s)' % {
                            'ch_link': i['channel_private_link'] if i['channel_private_link'] is not None else
                            't.me/' + i['channel_username'],
                            'ch_name': i['channel_name'],
                            'rt': '🔞' if '#explicit' in i['channel_tags'] else ''
                        }
                        ot.append(t)
                    other_txt += '\n'.join(ot)

                    sf = []
                    for i in sfw_channels:
                        t = '▪️ [%(ch_name)s](%(ch_link)s)' % {
                            'ch_link': i['channel_private_link'] if i['channel_private_link'] is not None else
                            't.me/' + i['channel_username'],
                            'ch_name': i['channel_name']
                        }
                        sf.append(t)
                    sfw_txt += '\n'.join(sf)

                    nsf = []
                    for i in nsfw_channels:
                        t = '▪️ [%(rt)s %(ch_name)s](%(ch_link)s)' % {
                            'ch_link': i['channel_private_link'] if i['channel_private_link'] is not None else
                            't.me/' + i['channel_username'],
                            'ch_name': i['channel_name'],
                            'rt': '🔞' if '#explicit' in i['channel_tags'] else ''
                        }
                        nsf.append(t)
                    nsfw_txt += '\n'.join(nsf)

                    import time
                    kb = telebot.types.InlineKeyboardMarkup()
                    b1 = telebot.types.InlineKeyboardButton("👁‍🗨 Join us now!", url='t.me/HalksNET')
                    kb.add(b1)
                    for channel in sfw_channels:
                            bot.send_message(channel['channel_id'], sfw_txt, parse_mode='markdown',
                                             reply_markup=kb).wait()
                            time.sleep(1)

                    for channel in nsfw_channels:
                            bot.send_message(channel['channel_id'], nsfw_txt, parse_mode='markdown',
                                             reply_markup=kb).wait()
                            time.sleep(1)

                    for channel in other_channels:
                            bot.send_message(channel['channel_id'], other_txt, parse_mode='markdown',
                                             reply_markup=kb).wait()
                            time.sleep(1)
                    return

        if reason == 'broadcast':
            pass

        if reason == 'admin_broadcast':
            msg = spl_data[1].split('=')[1]

            if msg == 'waiting':
                txt = 'Please, send the message title be sent to admins.'

                gl.send_admin_message = utils.Dictionary({'queue': 'title', 'message': utils.Dictionary({
                    'type': None,
                    'caption': None,
                    'text': None,
                    'file_id': None,
                    'title': None
                })})

                return bot.edit_message_text(txt, cid, call.message.message_id, call.id)

        if reason == 'add_networkers':
            # This part is to know if the call stack for adding admins was previously made.
            # Here, we get the whole deep link cache.
            cache_view = deep_link_cache.view()

            # Here, we get all deep link calls that have the 'add_admin' call

            ly = {i: cache_view[i]['data']
                  for i in cache_view if 'call' in cache_view[i]['data'] and
                  cache_view[i]['data']['call'] == 'add_networker'}

            # Finally, generates the code if the editing channel has not been previously cached to add admin; uses
            # The previous code otherwise.
            codes = [i for i in ly]
            code = codes[0] if len(ly) > 0 else utils.str_generator(8)
            label = '**Join Us!**'
            ttxt = '\n' \
                   'Become now a part of our network by clicking on this following link:\n' \
                   't.me/LilianRobot?start=%s' % code
            l_txt = 'https://t.me/share/url?url={label}&text={txt}'.format(
                label=label.replace(" ", "%20"),
                txt=ttxt.replace(" ", "%20").replace("/", "%2F").replace(":", "%3A").replace("?", "%3F").
                    replace("=", "%3D").replace('\n', '%0A'))
            txt = '[Click Here and share](%s) the invite.\n\n' \
                  'Remember, this link will automatically expire in height hours, and will no longer be available' \
                  ' to add new admins.' % l_txt
            if code not in ly:
                deep_link_cache.add(code, {'call': 'add_networker'}, (8 * 60 * 60))

            bot.send_message(chat_id=cid, text=txt, parse_mode='markdown')
