#!/usr/bin/env python

import datetime
import logging
import os
import re
import shutil
from glob import glob
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import requests
from plotly.subplots import make_subplots

logging.basicConfig(encoding="utf-8", level=logging.INFO)


LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


def get_files() -> list[str]:
    """get list of csv files from dropbox"""
    DROPBOX_URL = "https://www.dropbox.com/sh/f0j8xol7y0qbeg7/AADTapK4KX_nH-0WyUX67rsJa?dl=1"

    response = requests.get(DROPBOX_URL, timeout=20)
    open("data.zip", "wb").write(response.content)

    shutil.unpack_archive("data.zip", "data")
    os.remove("data.zip")

    list_of_files = glob("data/*.csv")
    return list_of_files


def read_file(filename: str):
    """read one csv file, returning a pandas.DataFrame"""
    text = open(filename).read()
    text_splitted = re.split("(.+\n[\*,]+\n)", text)
    text_splitted = text_splitted[1:]
    data = pd.read_csv(
        StringIO(text_splitted[9]), header=None, parse_dates=[[0, 1]], dayfirst=False
    )
    data.columns = ["date", "temperature", "humidity"]
    data = data.set_index("date")
    data = data.tz_localize("UTC")
    data = data.tz_convert(LOCAL_TIMEZONE)
    return data


def remove_begin_end(df, start_delay=pd.Timedelta("20m"), stop_delay=pd.Timedelta("1m")):
    """remove data from beginning and ending"""
    return df[(df.index > df.index.min() + start_delay) & (df.index < df.index.max() - stop_delay)]


if __name__ == "__main__":
    logging.info("downloading data")
    list_of_files = get_files()
    logging.info("reading data")
    data = [remove_begin_end(read_file(filename)) for filename in list_of_files]
    data = pd.concat(data)
    data = data.sort_index()
    print(data.index.min(), data.index.max())

    # not plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(template="plotly_white")
    fig.add_trace(
        go.Scatter(x=data.index, y=data.temperature, name="temperature"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=data.index, y=data.humidity, name="humidity"),
        secondary_y=True,
    )

    fig.update_xaxes(title_text="date")

    # Set y-axes titles
    fig.update_yaxes(title_text="temperature", secondary_y=False)
    fig.update_yaxes(title_text="humidity", secondary_y=True)

    for v in pd.date_range(data.index.min(), data.index.max(), freq="D", normalize=True)[1:]:
        fig.add_vline(v, line_dash="dot")

    logging.info("saving plot")
    fig.write_html("plot.html")
