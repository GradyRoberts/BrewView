# -*- coding: utf-8 -*-

import atexit
import json
import os
import requests
from math import pi
from datetime import datetime

from bokeh.embed import components
from bokeh.models import HoverTool, ColumnDataSource, DatetimeTickFormatter
from bokeh.plotting import figure
from bokeh.resources import CDN
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Dev
from config import weather_key, pi_key

# Production
#weather_key = os.environ['weather_key']
#pi_key = os.environ['pi_key']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temperature.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
db = SQLAlchemy(app)

class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isOutside = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    temp_C = db.Column(db.Float, nullable=False)
    temp_F = db.Column(db.Float, nullable=False)

    def __repr__(self):
        place = 'Outside' if self.isOutside else 'Inside'
        return f'<{place}Temp {self.id}: ({self.timestamp.time()}, {self.temp_F})>'

def make_plot():
    inside = Temperature.query.filter_by(isOutside=False).order_by(Temperature.timestamp).all()
    outside = Temperature.query.filter_by(isOutside=True).order_by(Temperature.timestamp).all()
    max_points = len(inside) if len(inside) < len(outside) else len(outside)

    inside_time = []
    inside_temp = []
    outside_time = []
    outside_temp = []
    if max_points > 0:
        inside_time = [t.timestamp for t in inside][-max_points:]
        inside_temp = [t.temp_F for t in inside][-max_points:]
        
        outside_time = [t.timestamp for t in outside][-max_points:]
        outside_temp = [t.temp_F for t in outside][-max_points:]

    data = {
        'inside_time': inside_time,
        'inside_temp': inside_temp,
        'outside_time': outside_time,
        'outside_temp': outside_temp,
    }
    source = ColumnDataSource(data)

    inside_hover = HoverTool(
        tooltips=[
            ('Time', '@inside_time{%m/%d %I:%M:%S %p}'),
            ('Inside', '@inside_temp{0.00}'),
        ],

        formatters={
            '@inside_time': 'datetime',
        },

        mode='vline'
    )
    outside_hover = HoverTool(
        tooltips=[
            ('Time', '@outside_time{%m/%d %I:%M:%S %p}'),
            ('Outside', '@outside_temp{0.00}'),
        ],

        formatters={
            '@outside_time': 'datetime',
        },

        mode='vline'
    )

    p = figure(plot_width=700, plot_height=700, tools=[inside_hover, outside_hover], title="Temperature over time", background_fill_color="#EFEFEF", x_axis_type='datetime')
    p.xaxis.formatter = DatetimeTickFormatter(
        microseconds = [r"%m/%d %I:%M:%S %p"],
        milliseconds = [r"%m/%d %I:%M:%S %p"],
        seconds = [r"%m/%d %I:%M:%S %p"],
        minsec = [r"%m/%d %I:%M:%S %p"],
        minutes=[r"%m/%d %I:%M:%S %p"],
        hourmin=[r"%m/%d %I:%M:%S %p"],
        hours=[r"%m/%d %I:%M:%S %p"],
        days=[r"%m/%d %I:%M:%S %p"],
        months=[r"%m/%d %I:%M:%S %p"],
        years=[r"%m/%d %I:%M:%S %p"],
    )
    p.xaxis.major_label_orientation = pi/4
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Temp (°F)'

    p.line('inside_time', 'inside_temp', line_color='blue', legend_label='Inside', source=source)
    inside_circle = p.circle('inside_time', 'inside_temp', line_color='black', fill_color='blue', size=5, source=source)
    p.line('outside_time', 'outside_temp', line_color='red', legend_label='Outside', source=source)
    outside_circle = p.circle('outside_time', 'outside_temp', line_color='black', fill_color='red', size=5, source=source)
    
    p.tools[0].renderers = [inside_circle]
    p.tools[1].renderers = [outside_circle]
    return components(p)

@app.route('/', methods=['GET'])
def index():
    script, div = make_plot()
    return render_template('index.html', script=script, div=div, resources=CDN.render())

@app.route('/add-data/inside/', methods=['POST'])
def add_inside_data():
    # Incoming temperature data from temp probe
    key = request.form['key']
    if key != pi_key:
        print(f"{datetime.now()} - Unauthorized upload attempt using key {key} from {request.remote_addr}.")
        return redirect('/')

    temp_C = request.form['temp_C']
    temp_F = request.form['temp_F']
    new_temp = Temperature(isOutside=False, temp_C=temp_C, temp_F=temp_F)
    try:
        db.session.add(new_temp)
        db.session.commit()
        print(f"{datetime.now()} - Added internal temp ({temp_C}, {temp_F})")
        return f"{datetime.now()} - Successfully added internal temp ({temp_C},{temp_F})!"
    except:
        return 'There was a problem adding internal temp'

@app.route('/add-data/outside/', methods=['POST'])
def add_outside_data():
    # Incoming temperature data from weather API
    key = request.form['key']
    if key != probe_key:
        print(f"{datetime.now()} - Unauthorized upload attempt using key {key} from {request.remote_addr}.")
        return redirect('/')

    temp_C = request.form['temp_C']
    temp_F = request.form['temp_F']
    new_temp = Temperature(isOutside=True, temp_C=temp_C, temp_F=temp_F)
    try:
        db.session.add(new_temp)
        db.session.commit()
        print(f"{datetime.now()} - Added external temp ({temp_C}, {temp_F})")
        return f"{datetime.now()} - Successfully added external temp ({temp_C},{temp_F})!"
    except:
        return 'There was a problem adding external temp'

@app.errorhandler(400)
def handle_bad_request(error):
    return 'Error 400: Bad Request'
@app.errorhandler(404)
def handle_bad_request(error):
    return 'Error 404: Page does not exist'


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)