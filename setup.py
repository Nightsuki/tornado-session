#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

VERSION = "1.0.0"

setup(name="Tornado-session",
      version=VERSION,
      description="Tornado-session is a Session manager with Redis for Tornado web framework.",
      author="Nightsuki",
      author_email="i@ymr.me",
      license="MIT License",
      url="http://github.com/Nightsuki/tornado-session",
      keywords=["Session", "Redis", "Tornado"],
      packages=["tornadosession"])
