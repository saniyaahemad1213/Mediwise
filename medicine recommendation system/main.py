from flask import Flask, request, render_template, jsonify
from flask import Flask, request, jsonify
import requests
from urllib.parse import quote
# Import jsonify
import numpy as np

import pandas as pd
import pickle
import os


# flask app
app = Flask(__name__)

# Get the absolute path to the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def dataset_path(filename):
    return os.path.join(BASE_DIR, 'datasets', filename)

def model_path(filename):
    return os.path.join(BASE_DIR, 'models', filename)

# load databasedataset===================================
sym_des = pd.read_csv(dataset_path("symtom_df.csv"))
precautions = pd.read_csv(dataset_path("precautions_df.csv"))
workout = pd.read_csv(dataset_path("workout_df.csv"))
description = pd.read_csv(dataset_path("description.csv"))
medications = pd.read_csv(dataset_path('medications.csv'))
diets = pd.read_csv(dataset_path("diets.csv"))


# load model===========================================
svc = pickle.load(open(model_path('svc.pkl'), 'rb'))


#============================================================
# custome and helping functions
#==========================helper funtions================


def helper(dis):
    
    desc = description[description['Disease'] == dis]['Description']
    desc = " ".join([str(w) for w in desc])

    pre = precautions[precautions['Disease'] == dis][['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']]
    pre = pre.values.tolist()  # Convert to list of lists

    med = medications[medications['Disease'] == dis]['Medication']
    med = med.values.tolist()  # Convert to list

    die = diets[diets['Disease'] == dis]['Diet']
    die = die.values.tolist()  # Convert to list

    wrkout = workout[workout['disease'] == dis]['workout']
    wrkout = wrkout.values.tolist()  # Convert to list

    return desc, pre, med, die, wrkout

import pickle

# Load feature_names from features.pkl
with open(model_path('features.pkl'), 'rb') as f:
    feature_names = pickle.load(f)

# Build symptoms_dict dynamically
symptoms_dict = {feat: idx for idx, feat in enumerate(feature_names)}
diseases_list = {15: 'Fungal infection', 4: 'Allergy', 16: 'GERD', 9: 'Chronic cholestasis', 14: 'Drug Reaction', 33: 'Peptic ulcer diseae', 1: 'AIDS', 12: 'Diabetes ', 17: 'Gastroenteritis', 6: 'Bronchial Asthma', 23: 'Hypertension ', 30: 'Migraine', 7: 'Cervical spondylosis', 32: 'Paralysis (brain hemorrhage)', 28: 'Jaundice', 29: 'Malaria', 8: 'Chicken pox', 11: 'Dengue', 37: 'Typhoid', 40: 'hepatitis A', 19: 'Hepatitis B', 20: 'Hepatitis C', 21: 'Hepatitis D', 22: 'Hepatitis E', 3: 'Alcoholic hepatitis', 36: 'Tuberculosis', 10: 'Common Cold', 34: 'Pneumonia', 13: 'Dimorphic hemmorhoids(piles)', 18: 'Heart attack', 39: 'Varicose veins', 26: 'Hypothyroidism', 24: 'Hyperthyroidism', 25: 'Hypoglycemia', 31: 'Osteoarthristis', 5: 'Arthritis', 0: '(vertigo) Paroymsal  Positional Vertigo', 2: 'Acne', 38: 'Urinary tract infection', 35: 'Psoriasis', 27: 'Impetigo'}

# Model Prediction function
def get_predicted_value(patient_symptoms):
    input_vector = np.zeros(len(symptoms_dict))
    for item in patient_symptoms:
        input_vector[symptoms_dict[item]] = 1
    return diseases_list[svc.predict([input_vector])[0]]




# creating routes========================================


@app.route("/")
def index():
    return render_template("index.html")

# Define a route for the home page
@app.route('/predict', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        symptoms = request.form.get('symptoms')
        print(symptoms)
        if symptoms == "Symptoms":
            message = "Please either write symptoms or you have written misspelled symptoms"
            return render_template('results.html', message=message)
        else:
            user_symptoms = [s.strip() for s in symptoms.split(',')]
            user_symptoms = [symptom.strip("[]' ") for symptom in user_symptoms]

            try:
                predicted_disease = get_predicted_value(user_symptoms)
            except KeyError:
                # This can happen if symptom not in symptoms_dict, handle gracefully
                message = "Symptoms not recognized. Please check your input."
                return render_template('results.html', message=message)

            # Check if predicted disease exists in your description dataset
            if predicted_disease not in description['Disease'].values:
                message = f"Disease '{predicted_disease}' not found in database."
                return render_template('results.html', message=message)

            dis_des, precautions, medications, rec_diet, workout = helper(predicted_disease)

            my_precautions = []
            if precautions and len(precautions) > 0:
                my_precautions = [p for p in precautions[0] if p]

            return render_template('results.html',
                                predicted_disease=predicted_disease,
                                dis_des=dis_des,
                                my_precautions=my_precautions,
                                medications=medications,
                                my_diet=rec_diet,
                                workout=workout)
# Or your form page for GET requests
    return render_template('index.html')



@app.route('/find_doctors', methods=['POST'])
def find_doctors():
    location = request.json.get('location')

    if not location:
        return jsonify({'error': 'No location provided'}), 400

    geo_url = f'https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1'
    headers = {'User-Agent': 'MediWiseApp/1.0 (your_email@example.com)'}  # Use a real email

    try:
        geo_resp = requests.get(geo_url, headers=headers, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
    except Exception as e:
        return jsonify({'error': f'Geocoding failed: {str(e)}'}), 500

    if not geo_data or not isinstance(geo_data, list) or not geo_data[0].get('lat') or not geo_data[0].get('lon'):
        return jsonify({'error': 'Location not found'}), 404

    lat = float(geo_data[0]['lat'])
    lon = float(geo_data[0]['lon'])

    # 🩺 Query Overpass API for doctors around the location
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    node
    [amenity=doctors]
    (around:3000,{lat},{lon});
    out;
    """
    try:
        overpass_resp = requests.post(overpass_url, data=overpass_query, headers=headers, timeout=15)
        overpass_resp.raise_for_status()
        overpass_data = overpass_resp.json()
    except Exception as e:
        return jsonify({'error': f'Overpass API failed: {str(e)}'}), 500

    doctors = []
    for element in overpass_data.get('elements', []):
        name = element.get('tags', {}).get('name', 'Unknown Doctor')
        address = element.get('tags', {}).get('addr:full') or "No address provided"
        doctors.append({
            "lat": element['lat'],
            "lon": element['lon'],
            "name": name,
            "address": address
        })

    # fallback if none found
    

    return jsonify({'doctors': doctors, 'center': {'lat': lat, 'lon': lon}})


if __name__ == '__main__':

    app.run(debug=True)