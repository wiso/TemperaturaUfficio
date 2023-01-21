#!/usr/bin/env python

import os
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

template = env.get_template("index.html")

today = datetime.datetime.today()
triggered_by = os.environ.get("GITHUB_EVENT_NAME")
if triggered_by == "push":
    triggered_by = "push on gitlab"
elif triggered_by == "repository_dispatch":
    triggered_by = "new data"
elif triggered_by == "workflow_dispatch":
    triggered_by = "manual build"

html = template.render(
    today="%s" % today.strftime("%d/%m/%Y"),
    triggered_by=triggered_by,
    branch=os.environ.get("GITHUB_REF_NAME"),
)

with open("index.html", mode="w", encoding="utf-8") as f:
    f.write(html)

for k, v in os.environ.items():
    print(k, v)
