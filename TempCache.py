import sys
import logging
import time
import gc
import utils
try:
    import Queue as queue
except ImportError:
    import queue
logger = logging.getLogger('TEMPCACHE')
console_logger = logging.StreamHandler(sys.stderr)
console_logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: %(message)s"
)
console_logger.setFormatter(formatter)
logger.addHandler(console_logger)
logger.setLevel(logging.ERROR)

gc.enable()


class KeyNotAddedError(Exception):
    pass


class TempCache:
    def __init__(self, name=None, bot=None):
        self.cache = {}

        self.bot = bot

        self.enabled_cleaner = True
        self.running = False
        self.paused = False
        self.process_time = time.process_time
        self.name = name

        self.__cleaner()

    def read(self, key):
        if not self._is_cached(key):
            return None
        value = self.cache[key].data
        logging.debug("ProcessTime: " + str(self.process_time()))
        return value

    def add(self, key, value, secs):
        # Awaits the running cleaner to end, before it edits the cache
        self.__wait_until_complete()

        self.paused = True
        time_cache = get_time(secs)
        self.cache[key] = utils.Dictionary({'time_set': time_cache, 'data': value})

        if not self._is_cached(key):
            logger.error("Key wasn't added properly")
            raise KeyNotAddedError
        logger.debug("Added {0} to cache {1} // ProcessTime: {2}".format(key, self.name, self.process_time()))
        self.paused = False
        return key

    def update(self, key, value, secs):
        self.paused = True
        time_cache = get_time(secs)
        self.cache[key] = utils.Dictionary({'time_set': time_cache, 'data': value})
        logger.debug("Updated key {0} with the values {1} to cache {2} // ProcessTime: {3}".format(key, value,
                                                                                                   self.name,
                                                                                                   time.process_time()))
        self.paused = False
        return key

    def remove(self, key):
        if not self._is_cached(key):
            return True
        self.__wait_until_complete()
        self.paused = True
        del self.cache[key]
        self.paused = False
        return True

    def view(self):
        return self.cache

    def stop(self):
        logger.info("Stopped MemCacheCleaner for {0}".format(self.name))
        self.enabled_cleaner = False

    def __wait_until_complete(self):
        while self.running:
            pass

    @utils.async()
    def __cleaner(self):
        logger.info("Started MemCacheCleaner for {0}".format(self.name))

        while self.enabled_cleaner:
            while self.paused:
                pass
            self.running = True

            time_now = time.time
            pop = [i for i in self.cache if self.cache[i]['time_set'] <= time_now()]
            for i in pop:
                self.cache.pop(i, None)
            self.running = False

            time.sleep(1)

    def _is_cached(self, key):
        if key not in self.cache:
            return False
        return True


def get_time(secs):
    return abs(int(secs) + int(time.time()))


reactions_cache = TempCache(name='reactions_cache')
deep_link_cache = TempCache(name='deep_link_cache')
