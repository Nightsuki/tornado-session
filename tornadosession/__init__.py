import uuid
import hashlib
from tornado import gen
import codecs
from tornado.websocket import WebSocketHandler
import time

try:
    import cPickle as pickle
except:
    import pickle


class SessionBaseHandler(WebSocketHandler):
    cookie_config = {}
    session_config = {}
    redis = None

    def initialize(self):
        self.session_config = self.settings.get("session")
        self.config_handle()
        try:
            self.redis = self.settings.get("session_redis")
        except Exception as e:
            print(e)

    def config_handle(self):
        if "expires" in self.session_config["cookie_config"]:
            self.cookie_config["expires"] = int(time.time()) + self.session_config["cookie_config"]["expires"]
        if "domain" in self.session_config["cookie_config"]:
            self.cookie_config["domain"] = self.session_config["cookie_config"]["domain"]
        if "httponly" in self.session_config["cookie_config"]:
            self.cookie_config["httponly"] = self.session_config["cookie_config"]["httponly"]
        if "secret" in self.session_config["cookie_config"]:
            self.application.settings["cookie_secret"] = self.session_config["cookie_config"]["secret"]

    @property
    def session_id(self):
        return self.get_secure_cookie("session_id") if self.get_secure_cookie("session_id") else self._generate_id()

    def get_current_user(self):
        return self.get_session()

    @gen.coroutine
    def _get_user(self, session_id):
        try:
            user_id = yield gen.Task(self.redis.get, session_id)
            raw_data = yield gen.Task(self.redis.get, user_id)
            if raw_data:
                user = pickle.loads(codecs.decode(raw_data.encode(), "base64"))
                raise gen.Return(user)
            else:
                raise gen.Return(None)
        except IOError:
            raise gen.Return(None)

    @staticmethod
    def _generate_id():
        temp = str(uuid.uuid4())
        new_id = hashlib.sha256(temp.encode("utf-8"))
        return new_id.hexdigest()

    @gen.coroutine
    def del_session(self):
        yield gen.Task(self.redis.delete, self.session_id)

    @gen.coroutine
    def get_session(self, session_id=None):
        session_id = self.get_secure_cookie("session_id") if not session_id else session_id
        if session_id:
            user = yield self._get_user(session_id)
            if user:
                raise gen.Return(user)
        raise gen.Return(None)

    @gen.coroutine
    def set_session(self, user):
        session_data = codecs.encode(pickle.dumps(user), "base64").decode()
        session_id = self.session_id
        self.set_secure_cookie("session_id", session_id, **self.cookie_config)
        yield gen.Task(self.redis.set, "user_{}".format(user.id), session_data)
        yield gen.Task(self.redis.set, session_id, "user_{}".format(user.id), ex=60 * 60 * 24)

    @gen.coroutine
    def refresh_session(self, user):
        session_data = pickle.dumps(user)
        yield gen.Task(self.redis.set, "user_{}".format(user.id), session_data)
