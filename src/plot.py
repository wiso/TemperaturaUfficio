#!/usr/bin/env python

"""Make the plot downloading data from Dropbox."""

import datetime
import logging
import os
import re
import shutil
from glob import glob
from io import StringIO

import pandas as pd
import requests
from plotly import graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(encoding="utf-8", level=logging.INFO)


LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
DROPBOX_URL = "https://www.dropbox.com/sh/f0j8xol7y0qbeg7/AADTapK4KX_nH-0WyUX67rsJa?dl=1"


def get_files() -> list[str]:
    """Return a list of csv files from dropbox."""
    response = requests.get(DROPBOX_URL, timeout=20)
    with open("data.zip", "wb") as tmp_file:
        tmp_file.write(response.content)

    shutil.unpack_archive("data.zip", "data")
    os.remove("data.zip")

    return glob("data/*.csv")


def read_file(filename: str):
    """Read one csv file, returning a pandas.DataFrame."""
    text = open(filename).read()
    text_splitted = re.split("(.+\n[\\*,]+\n)", text)
    text_splitted = text_splitted[1:]
    sensor_data = pd.read_csv(
        StringIO(text_splitted[9]), header=None, parse_dates=[[0, 1]], dayfirst=False
    )
    sensor_data.columns = ["date", "temperature", "humidity"]
    sensor_data.set_index("date").tz_localize("UTC").tz_convert(LOCAL_TIMEZONE)
    return sensor_data


def remove_begin_end(sensor_data, start_delay=pd.Timedelta("20m"), stop_delay=pd.Timedelta("1m")):
    """Remove data from beginning and ending."""
    return sensor_data[
        (sensor_data.index > sensor_data.index.min() + start_delay)
        & (sensor_data.index < sensor_data.index.max() - stop_delay)
    ]


if __name__ == "__main__":
    logging.info("downloading data")
    list_of_files = get_files()
    logging.info("reading data")
    data = [remove_begin_end(read_file(filename)) for filename in list_of_files]
    data = pd.concat(data)
    data = data.sort_index()
    print(data.index.min(), data.index.max())

    # now plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(template="plotly_dark")
    fig.add_trace(
        go.Scatter(x=data.index, y=data.temperature, name="temperature", line_color="#EF553B"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data.humidity,
            name="humidity",
            line_color="#202AB6",
            visible="legendonly",
        ),
        secondary_y=True,
    )

    fig.update_yaxes(
        title_text="temperature",
        ticklen=10,
        linewidth=1,
        linecolor="white",
        tickcolor="white",
        ticks="inside",
        secondary_y=False,
        mirror=True,
        showline=True,
        minor=dict(ticklen=6, tickcolor="white", ticks="inside", showgrid=True),
    )
    fig.update_yaxes(
        title_text="humidity",
        ticklen=10,
        tickcolor="white",
        ticks="inside",
        secondary_y=True,
        showgrid=False,
        zeroline=False,
        minor=dict(ticklen=6, tickcolor="white", ticks="inside", showgrid=False),
    )

    fig.update_xaxes(
        ticklen=10,
        linewidth=1,
        linecolor="white",
        tickcolor="white",
        ticks="inside",
        showline=True,
        mirror="all",
    )

    for v in pd.date_range(data.index.min(), data.index.max(), freq="D", normalize=True)[1:]:
        fig.add_vline(v, line_dash="dot", line_color="#777")

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
        template="plotly_dark",
    )

    logging.info("saving plot")
    fig.write_html("plot.html")
