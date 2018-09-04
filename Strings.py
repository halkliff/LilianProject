# String Handlers & Buttons
import telebot

Admin = {
    'stats': {},
    'channels': {
        'channels': {
            'text': "*Channel List Administration*\n\nSelect an option:",
            'buttons': [[telebot.types.InlineKeyboardButton("Add a Channel",
                                                            callback_data='admin=channels add_channel=True'),
                         telebot.types.InlineKeyboardButton("Edit a Channel",
                                                            callback_data='admin=channels edit_channel=True')],
                        [telebot.types.InlineKeyboardButton("Delete a channel",
                                                            callback_data='admin=channels delete_channel=True')]],
                },

        'edit_new_channel_info': {
            'channel_creator': {
                'text': "What would you like to change?",
                'buttons': [[telebot.types.InlineKeyboardButton("Creator Name",
                                                                callback_data='admin=channels edit_new_channel_info='
                                                                              'channel_creator_name'),
                             telebot.types.InlineKeyboardButton("Creator Username",
                                                                callback_data='admin=channels edit_new_channel_info='
                                                                              'channel_creator_username')],
                            [telebot.types.InlineKeyboardButton("Cancel", callback_data='admin=channels back=True')]
                            ]
            },
            'channel_creator_name': {
                'text': "Send the new Channel creator Name.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel",
                                                                callback_data='admin=channels edit_new_channel_info='
                                                                              'channel_creator')]]
            },
            'channel_creator_username': {
                'text': "Send the new Channel creator Username.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel",
                                                                callback_data='admin=channels edit_new_channel_info='
                                                                              'channel_creator')]]
            },
            'name': {
                'text': "Send the new Channel Name.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel", callback_data='admin=channels back=True')]]
            },
            'info': {
                'text': "Send the new Channel Info.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel", callback_data='admin=channels back=True')]]
            },
            'username': {
                'text': "Send the new Channel Username.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel", callback_data='admin=channels back=True')]]
            },
            'link': {
                'text': "Send the new Channel Private Link.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel", callback_data='admin=channels back=True')]]
            },
            'profile_pic': {
                'text': "Send the new Channel Profile Picture.",
                'buttons': [[telebot.types.InlineKeyboardButton("Cancel", callback_data='admin=channels back=True')]]
            }

        },
    }
}


Channel = {
    'editing': {
        'name': 'Editing the *Name*.\n\nPlease, send your new Channel Name.',
        'description': 'Editing the *Description*.\n\nPlease, send your new Channel Description.',
        'username': 'Editing the *Alias*.\n\nPlease, send your new Channel `@alias`.',
        'link': 'Editing the *Private Link*. Please, send your new Channel Private Link\n(As in: '
                '`t.me/joinchat/Awqws123APWO-356QdpTu`)',
        'profile_pic': 'Editing the *Profile Picture*. Please, send the new Picture for your Profile Picture.',
        'tags': 'Editing the *Channel Tags*. Please, send the #tags in sequence.'
    }
}
