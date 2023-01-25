#!/usr/bin/env python

"""Render the html template and produce the html."""

import datetime
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader('templates'), autoescape=select_autoescape())

template = env.get_template('index.html')

today = datetime.datetime.today()
triggered_by = os.environ.get('GITHUB_EVENT_NAME')
if triggered_by is not None:
    triggered_by = {
        'push': 'push on gitlab',
        'repository_dispatch': 'new_data',
        'workflow_dispatch': 'manual build',
    }.get(triggered_by, triggered_by)

html = template.render(
    today=today.strftime('%d/%m/%Y'),
    triggered_by=triggered_by,
    branch=os.environ.get('GITHUB_REF_NAME'),
)

with open('index.html', mode='w', encoding='utf-8') as f:
    f.write(html)
