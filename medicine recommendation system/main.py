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
# Load disease names in the same order as your model's output
with open(model_path('diseases.pkl'), 'rb') as f:
    diseases_list = pickle.load(f)

# Model Prediction function
def get_predicted_value(patient_symptoms):
    input_vector = np.zeros(len(symptoms_dict))
    for item in patient_symptoms:
        if item in symptoms_dict:
            input_vector[symptoms_dict[item]] = 1
    pred_idx = svc.predict([input_vector])[0]
    return diseases_list[pred_idx]





# creating routes========================================

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')
@app.route("/")
def index():
    return render_template("index.html")
@app.route('/symptom_checker')
def symptom_checker():
    return render_template('symptom_checker.html')
# Define a route for the home page
@app.route('/predict', methods=['POST'])
def predict():
    # Try to get JSON data first
    if request.is_json:
        symptoms = request.json.get('symptoms')
    else:
        symptoms = request.form.get('symptoms')
    if not symptoms or symptoms.strip().lower() == "symptoms":
        return jsonify({"error": "Please enter your symptoms."}), 400

    user_symptoms = [s.strip() for s in symptoms.split(',')]
    user_symptoms = [symptom.strip("[]' ") for symptom in user_symptoms]

    try:
        predicted_disease = get_predicted_value(user_symptoms)
    except Exception:
        return jsonify({"error": "Symptoms not recognized. Please check your input."}), 400

    if predicted_disease not in description['Disease'].values:
        return jsonify({"error": f"Disease '{predicted_disease}' not found in database."}), 404

    dis_des, precautions, medications, rec_diet, workout = helper(predicted_disease)
    my_precautions = []
    if precautions and len(precautions) > 0:
        my_precautions = [p for p in precautions[0] if p]

    return jsonify({
        "predicted_disease": predicted_disease,
        "description": dis_des,
        "precautions": my_precautions,
        "medications": medications,
        "diet": rec_diet,
        "workout": workout
    })

@app.route('/find_doctors', methods=['GET'])
def find_doctors_page():
    return render_template('find_doctors.html')

@app.route('/api/find_doctors', methods=['POST'])
def find_doctors_api():
    location = request.json.get('location')
    if not location:
        return jsonify({'error': 'No location provided'}), 400

    # Geocode location
    geo_url = f'https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1'
    geo_resp = requests.get(geo_url, headers={'User-Agent': 'MediwiseApp'})
    geo_data = geo_resp.json()
    if not geo_data:
        return jsonify({'error': 'Location not found'}), 404
    lat = float(geo_data[0]['lat'])
    lon = float(geo_data[0]['lon'])

    # Overpass API query
    radius = 5000
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="doctors"](around:{radius},{lat},{lon});
      node["healthcare"="doctor"](around:{radius},{lat},{lon});
    );
    out body;
    """
    response = requests.post("https://overpass-api.de/api/interpreter", data=overpass_query)
    osm_data = response.json()
    doctors_found = []

    for element in osm_data.get('elements', []):
     if element['type'] == 'node':
        tags = element.get('tags', {})
        name = tags.get('name', 'Doctor')
        address = tags.get('addr:street', 'Address not specified')
        specialty = tags.get('speciality') or tags.get('specialty') or "General"
        phone = tags.get('phone') or tags.get('contact:phone') or "Not available"
        doctors_found.append({
            "name": name,
            "lat": element['lat'],
            "lon": element['lon'],
            "address": address,
            "specialty": specialty,
            "phone": phone
        })
            
    return jsonify({
        "center": {"lat": lat, "lon": lon},
        "doctors": doctors_found
    })
    # ...inside your find_doctors_api route...

if __name__ == '__main__':

    app.run(debug=True)