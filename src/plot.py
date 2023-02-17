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
from plotly import graph_objects as go  # type: ignore
from plotly.subplots import make_subplots  # type: ignore

logging.basicConfig(level=logging.INFO)


LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
DROPBOX_URL = 'https://www.dropbox.com/sh/f0j8xol7y0qbeg7/AADTapK4KX_nH-0WyUX67rsJa?dl=1'


def get_files() -> list[str]:
    """Return a list of csv files from dropbox."""
    response = requests.get(DROPBOX_URL, timeout=20)
    with open('data.zip', 'wb') as tmp_file:
        tmp_file.write(response.content)

    shutil.unpack_archive('data.zip', 'data')
    os.remove('data.zip')

    return glob('data/*.csv')


def read_file(filename: str) -> pd.DataFrame:
    """Read one csv file, returning a pandas.DataFrame."""
    with open(filename, 'r', encoding='utf8') as data_file:
        text = data_file.read()
    text_splitted = re.split('(.+\n[\\*,]+\n)', text)
    text_splitted = text_splitted[1:]
    sensor_data = pd.read_csv(
        StringIO(text_splitted[9]),
        header=None,
        parse_dates=[[0, 1]],
        dayfirst=False,
    )
    return (
        sensor_data.set_axis(['date', 'temperature', 'humidity'], axis='columns')
        .set_index('date')
        .tz_localize('UTC')
        .tz_convert(LOCAL_TIMEZONE)
    )


def remove_begin_end(
    sensor_data: pd.DataFrame, start_delay=pd.Timedelta('20m'), stop_delay=pd.Timedelta('1m')
) -> pd.DataFrame:
    """Remove data from beginning and ending."""
    return sensor_data[
        (sensor_data.index > sensor_data.index.min() + start_delay)
        & (sensor_data.index < sensor_data.index.max() - stop_delay)
    ]


def get_weather_data():
    """get weather data from open meteo"""
    response = requests.get(
        'https://api.open-meteo.com/v1/forecast',
        params={
            'latitude': 45.476,
            'longitude': 9.23,
            'hourly': ['temperature_2m', 'precipitation'],
            'timezone': 'UTC',
            'start_date': '2023-01-01',
            'end_date': datetime.date.today().isoformat(),
        },
        timeout=60,
    )
    weather_data = response.json()

    df_weather_data = pd.DataFrame(weather_data['hourly'])
    df_weather_data['time'] = pd.to_datetime(df_weather_data['time']).dt.tz_localize(
        weather_data['timezone']
    )
    return df_weather_data.set_index('time')


if __name__ == '__main__':
    logging.info('downloading data')
    list_of_files = get_files()
    logging.info('reading data')
    data = pd.concat([remove_begin_end(read_file(filename)) for filename in list_of_files])
    data = data.sort_index()
    print(data.index.min(), data.index.max())

    df_weather = get_weather_data().sort_index()
    df_weather = df_weather.loc[
        (df_weather.index > data.index.min()) & (df_weather.index < data.index.max())
    ]

    mask_working_hours = data.index.time < datetime.time(19, 0, 0)  # type: ignore
    mask_working_hours &= data.index.time > datetime.time(7, 0, 0)  # type: ignore
    mask_working_hours &= data.index.weekday < 5  # type: ignore

    data_working = data[mask_working_hours]

    df = data_working.groupby(data_working.index.date)['temperature'].agg(
        [min, max, 'first', 'last']
    )

    # now plot
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.update_layout(template='plotly_dark')
    fig.add_trace(
        go.Scatter(x=data.index, y=data.temperature, name='temperature', line_color='#EF553B'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data.humidity,
            name='humidity',
            line_color='#202AB6',
            visible='legendonly',
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Candlestick(
            x=pd.DatetimeIndex(df.index) + datetime.timedelta(hours=13),  # type: ignore
            close=df['max'],
            open=df['min'],
            high=df['max'],
            low=df['min'],
            name='Min/Max in working days 7-19',
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_weather.index,
            y=df_weather['temperature_2m'],
            visible='legendonly',
            name='ext temperature',
        )
    )

    fig.update_yaxes(
        title_text='temperature',
        ticklen=10,
        linewidth=1,
        linecolor='white',
        tickcolor='white',
        ticks='inside',
        secondary_y=False,
        mirror=True,
        showline=True,
        minor={
            'ticklen': 6,
            'tickcolor': 'white',
            'ticks': 'inside',
            'showgrid': True,
        },
    )
    fig.update_yaxes(
        title_text='humidity',
        ticklen=10,
        tickcolor='white',
        ticks='inside',
        secondary_y=True,
        showgrid=False,
        zeroline=False,
        minor={'ticklen': 6, 'tickcolor': 'white', 'ticks': 'inside', 'showgrid': True},
    )

    fig.update_xaxes(
        ticklen=10,
        linewidth=1,
        linecolor='white',
        tickcolor='white',
        ticks='inside',
        showline=True,
        mirror='all',
    )

    for v in pd.date_range(data.index.min(), data.index.max(), freq='D', normalize=True)[1:]:
        fig.add_vline(v, line_dash='dot', line_color='#777')

    fig.update_layout(
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'left', 'x': 0.0},
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
    )

    logging.info('saving plot')
    fig.write_html('plot.html')
