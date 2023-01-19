#!/usr/bin/env python

from jinja2 import Environment, FileSystemLoader, select_autoescape
import datetime

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

template = env.get_template("index.html")

today = datetime.datetime.today()
html = template.render(the="variables", today="%s" % today)

with open("index.html", mode="w", encoding="utf-8") as f:
    f.write(html)
