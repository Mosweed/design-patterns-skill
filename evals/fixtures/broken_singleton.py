"""Application config 'singleton' used across our worker threads."""

import json


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, path="config.json"):
        self.path = path
        self.values = {}
        self.loaded = False

    def load(self):
        with open(self.path) as fh:
            self.values = json.load(fh)
        self.loaded = True

    def get(self, key, default=None):
        if not self.loaded:
            self.load()
        return self.values.get(key, default)


def get_config():
    return Config()
