import threading
# import re
import sys
import six
import random
# import hashlib
import string
from functools import wraps, partial
import config

# Python3 queue support.

try:
    import Queue
except ImportError:
    import queue as Queue


class AsyncWorker(threading.Thread):
        count = 0

        def __init__(self, exception_callback=None, queue=None, name=None):
            if not name:
                name = "AsyncWorker{0}".format(self.__class__.count + 1)
                self.__class__.count += 1
            if not queue:
                queue = Queue.Queue()

            threading.Thread.__init__(self, name=name)
            self.queue = queue
            self.daemon = True

            self.received_task_event = threading.Event()
            self.done_event = threading.Event()
            self.exception_event = threading.Event()
            self.continue_event = threading.Event()

            self.exception_callback = exception_callback
            self.exc_info = None
            self._running = True
            self.start()

        def run(self):
            while self._running:
                try:
                    task, args, kwargs = self.queue.get(block=True, timeout=.5)
                    self.continue_event.clear()
                    self.received_task_event.clear()
                    self.done_event.clear()
                    self.exception_event.clear()
                    self.received_task_event.set()

                    task(*args, **kwargs)
                    self.done_event.set()
                except Queue.Empty:
                    pass
                except:
                    self.exc_info = sys.exc_info()
                    self.exception_event.set()

                    if self.exception_callback:
                        self.exception_callback(self, self.exc_info)
                    self.continue_event.wait()

        def put(self, task):
            self.queue.put(task)

        def raise_exceptions(self):
            if self.exception_event.is_set():
                six.reraise(self.exc_info[0], self.exc_info[1], self.exc_info[2])

        def clear_exceptions(self):
            self.exception_event.clear()
            self.continue_event.set()

        def stop(self):
            self._running = False


class Threaded:

    def __init__(self, num_threads=2):
        self.tasks = Queue.Queue()
        self.workers = [AsyncWorker(self.on_exception, self.tasks) for _ in range(num_threads)]
        self.num_threads = num_threads

        self.exception_event = threading.Event()
        self.exc_info = None

    def put(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def on_exception(self, worker_thread, exc_info):
        self.exc_info = exc_info
        self.exception_event.set()
        worker_thread.continue_event.set()

    def raise_exceptions(self):
        if self.exception_event.is_set():
            six.reraise(self.exc_info[0], self.exc_info[1], self.exc_info[2])

    def clear_exceptions(self):
        self.exception_event.clear()

    def close(self):
        for worker in self.workers:
            worker.stop()
        for worker in self.workers:
            worker.join()


class AsyncTask:
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

        self.done = False
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.result = sys.exc_info()
            raise e
        self.done = True
        return self.result

    def wait(self):
        if not self.done:
            self.thread.join()
        if isinstance(self.result, BaseException):
            six.reraise(self.result[0], self.result[1], self.result[2])
        else:
            return self.result


def async():
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return AsyncTask(fn, *args, **kwargs)

        return wrapper

    return decorator


class Dictionary(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def str_generator(length):
    chars = string.ascii_letters + string.digits * length
    random_string = ''.join(random.sample(chars, length))

    return random_string


def id_encoder(n):
    # n = int(oct(n).replace('0o', ''))
    return hex(n).replace('0x', '') + str_generator(4)


def deep_link(txt):
    txt = txt.split()
    return txt[1] if len(txt) > 1 and txt[1] is not None else None


def report_msg(bot, m, gl, e, sexc, msg=None, mid=None):
    import telebot
    cid = m.chat.id
    report_code = str_generator(6)
    report = "User {0} ({1}) Reported the following issue:\n\n" \
             "{2}\n\n{3}\n\n" \
             "REPORT CODE: {4}\n\nMSG:{5}".format(cid, m.from_user.first_name, str(e), str(sexc), report_code, msg)
    if 'report' not in gl:
        gl.report = Dictionary()
    gl.report[report_code] = report
    txt = 'An error occurred. Please tap the button below to report it.'
    markup = telebot.types.InlineKeyboardMarkup()
    report_button = telebot.types.InlineKeyboardButton("✉️ Send Report",
                                                       callback_data="report={}".format(report_code))
    markup.add(report_button)
    if mid:
        bot.edit_message_text(chat_id=cid, message_id=mid, text=txt, reply_markup=markup)
    else:
        bot.send_message(cid, txt, reply_markup=markup)


@async()
def update_user_info(m):
    import Data
    uid = m.from_user.id
    uname = m.from_user.first_name
    uusername = m.from_user.username
    db = Data.Database(Data.users_db.members)
    return db.update({'user_id': uid}, {'$set':{'user_username': uusername, 'user_name': uname}})


# ============================================ DECORATORS FOR BOT FACILITY ============================================
def admin_access(log=None):
    def decorator(func=None):
        if func is None:
            # If called without method, we've been called with optional arguments.
            # We return a decorator with the optional arguments filled in.
            return partial(admin_access)
        import config

        @wraps(func)
        def wrapper(bot, m, *args, **kwargs):
            cid = m.from_user.id

            if cid not in config.BOT_SUDO:
                try:
                    txt = "You are not authorized to access this session."
                    bot.send_message(cid, txt)
                    return

                except Exception as e:
                    log.error(e)
                    return

            return func(bot, m, *args, **kwargs)

        return wrapper
    return decorator


def owner_access(log=None, db=None):
    def decorator(func=None):
        if func is None:
            # If called without method, we've been called with optional arguments.
            # We return a decorator with the optional arguments filled in.
            return partial(owner_access)

        @wraps(func)
        def wrapper(bot, m, *args, **kwargs):
            cid = m.chat.id
            if cid in config.BOT_SUDO:
                return func(bot, m, *args, **kwargs)
            owner = db.get({'user_id': int(cid)})
            if owner is None:
                try:
                    txt = "You are not authorized to access this session."
                    bot.send_message(cid, txt)
                    return
                except Exception as e:
                    log.error(e)
                    return

            return func(bot, m, *args, **kwargs)

        return wrapper
    return decorator

"""
import datetime
import time
print(datetime.date.today().isoformat().split('-')) # How we know the day, month and year
d = datetime.datetime.now() # date on the local (simulating date coming from user)
e = datetime.datetime.utcnow() # date on the server (simulating the date in server)
print(time.mktime(d.timetuple()) + d.microsecond / 1E6)  # Make the time based on the time provided by the user
print(time.time())                                       # For that, shall use datetime.datetime.format(month, day, hour, minute)
print((d.hour + (d.minute / 60)) - (e.hour + (58 / 60))) # Calculate the difference of the time between user and server
t = {'qyz': {'zaz':2}, 
     'zyz': {'pyw':1}, 
     'xyz': {'call': None}, 
     'pyz': {'call': 'add_admin', 'channel': None}, 
     'nyz': {'call': 'add_admin', 'channel': 123456}}
l = {t[i]['channel']: i for i in t if 'call' in t[i] and t[i]['call'] == 'add_admin'}
print(l)"""