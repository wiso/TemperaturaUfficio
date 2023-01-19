#!/usr/bin/env python

import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

template = env.get_template("index.html")

today = datetime.datetime.today()
html = template.render(today="%s" % today.strftime("%d %m %Y"))

with open("index.html", mode="w", encoding="utf-8") as f:
    f.write(html)

import os
for k, v in os.environ.items():
    print(k, v)