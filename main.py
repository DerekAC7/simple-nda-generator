from flask import Flask, render_template, request, redirect, url_for, session, make_response
from datetime import date
from xhtml2pdf import pisa
from io import BytesIO
import stripe
import json
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

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
    success_url = f"{YOUR_DOMAIN}/download?paid=1&data={encoded_data}"

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1Rgra4KtZU08gr8aurgZFYZE',
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=YOUR_DOMAIN + '/cancel',
    )
    return redirect(checkout_session.url, code=303)

@app.route('/cancel')
def cancel():
    return "Payment was cancelled. Please try again."

@app.route('/download')
def download_pdf():
    # Validate payment
    if not session.get('paid') and request.args.get('paid') != '1':
        return redirect(url_for('home'))

    # Prefer session data
    nda_data = session.get('nda_data')

    # If session is empty, fall back to data param
    if not nda_data:
        raw_data = request.args.get('data')
        if not raw_data:
            return "Missing NDA data.", 400
        try:
            decoded_json = urllib.parse.unquote(raw_data)
            nda_data = json.loads(decoded_json)
        except Exception as e:
            return f"Failed to parse NDA data: {e}", 400

    # Generate PDF
    nda_html = render_template('pdf_template.html', nda_data=nda_data)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(nda_html, dest=pdf)

    if pisa_status.err:
        return "PDF generation failed", 500

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=nda.pdf'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
