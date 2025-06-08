from flask import Flask, redirect, url_for, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

import pandas as pd
import requests
from datetime import datetime

client_id = 'atulyasharan29-api-client'
client_secret = 'vjg5hFd8yiSpsHobsFEqKsvj6IVnKCfj'

def get_access_token(client_id, client_secret):
    url = 'https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Access token retrieved successfully.")
        return response.json().get('access_token')
    else:
        print(f"Failed to retrieve access token. Status code: {response.status_code}")
        return None

def get_opensky_data(token):
    url = 'https://opensky-network.org/api/states/all'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Flight data retrieved.")
        data = response.json()
        columns = [
            "icao24", "callsign", "origin_country", "time_position", "last_contact",
            "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
            "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
            "spi", "position_source"
        ]
        df = pd.DataFrame(data["states"], columns=columns)
        return df
    else:
        print(f"Failed to retrieve flight data. Status code: {response.status_code}")
        return None

# --- MAIN ---





app = Flask(__name__)
app.secret_key = 'FUDHU'  # Required for FlaskForm CSRF protection

class CallSignForm(FlaskForm):
    callsign = StringField("Call Sign")
    submit = SubmitField("Search")

@app.route('/', methods=['GET', 'POST'])
def home():
    form = CallSignForm()
    if form.validate_on_submit():
        return redirect(url_for('tracker', callsign=form.callsign.data))
    token = get_access_token(client_id, client_secret)
    url = 'https://opensky-network.org/api/states/all'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Flight data retrieved.")
        data = response.json()
        print(data)

    return render_template('index.html', form=form,data= data)

@app.route('/<callsign>',methods = ['GET','POST'])
def tracker(callsign):
    form = CallSignForm()
    if form.validate_on_submit():
        return redirect(url_for('tracker', callsign=form.callsign.data))
    token = get_access_token(client_id, client_secret)
    
    if not token:
        print("Unable to continue without access token.")
        return "Access token error", 500

    df = get_opensky_data(token)
    if df is None:
        return "Failed to fetch data", 500

    # Filter by callsign (strip spaces from both sides to be safe)
    filtered = df[df["callsign"].str.strip() == callsign.strip()]
    
    if filtered.empty:
        print(f"No aircraft found with callsign: {callsign}")
        return render_template("index.html", form=None, error="No flight found.")

    # Get the first matching flight
    flight_dict = filtered.iloc[0].to_dict()
    print("Matching aircraft found:")
    print(flight_dict)
    url = 'https://opensky-network.org/api/states/all'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Flight data retrieved.")
        data = response.json()
    return render_template("index.html", flight=flight_dict, form=form,data = data)


if __name__ == '__main__':
    app.run(debug=False )
