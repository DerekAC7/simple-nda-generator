import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from datetime import date
from xhtml2pdf import pisa
from io import BytesIO
import stripe
import json
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Stripe config
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
YOUR_DOMAIN = 'https://7574f864-a1b3-4b31-bd4d-4b28320e378f-00-e600379fq3za.kirk.replit.dev'

@app.route('/')
def home():
    return render_template('index.html', date=date)

@app.route('/generate', methods=['POST'])
def generate():
    session.clear()
    nda_data = {
        'party1_name': request.form['party1_name'],
        'party1_address': request.form['party1_address'],
        'party2_name': request.form['party2_name'],
        'party2_address': request.form['party2_address'],
        'effective_date': request.form['effective_date'],
        'duration': request.form['duration'],
        'state_law': request.form['state_law'],
        'county': request.form['county'],
        'purpose': request.form['purpose'],
        'is_mutual': 'is_mutual' in request.form
    }

    if not nda_data['is_mutual']:
        nda_data['discloser'] = request.form['discloser']

    session['nda_data'] = nda_data
    return render_template('result.html', nda_data=nda_data)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    nda_data = session.get('nda_data')
    if not nda_data:
        return redirect(url_for('home'))

    encoded_data = urllib.parse.quote(json.dumps(nda_data))
    success_url = f"{YOUR_DOMAIN}/success?data={encoded_data}"

    checkout_session = st_
