from flask import Flask, request, render_template, jsonify, send_file
import requests
from urllib.parse import quote
# Import jsonify
import numpy as np

import pandas as pd
import pickle
import os

from fpdf import FPDF


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

    import ast

    def parse_list(val):
        # Handles both ["['A', 'B']"] and "['A', 'B']"
        if isinstance(val, list) and len(val) == 1 and isinstance(val[0], str) and val[0].startswith('['):
            try:
                return ast.literal_eval(val[0])
            except Exception:
                return val
        if isinstance(val, str) and val.startswith('['):
            try:
                return ast.literal_eval(val)
            except Exception:
                return [val]
        return val

    # After: dis_des, precautions, medications, rec_diet, workout = helper(predicted_disease)
    medications = parse_list(medications)
    Diet = parse_list(rec_diet)
    my_precautions = parse_list(precautions)
    workout = parse_list(workout)

    my_precautions = []
    if precautions and len(precautions) > 0:
        my_precautions = [p for p in precautions[0] if p]

    symptoms = request.form.get('symptoms', '')
    symptoms_list = [s.strip() for s in symptoms.split(',')] if symptoms else []

    return render_template(
        'results.html',
        predicted_disease=predicted_disease,
        dis_des=dis_des,
        my_precautions=my_precautions,
        medications=medications,
        my_diet=Diet,
        workout=workout,
        symptoms=symptoms_list
    )

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





def get_recommendations(disease):
    # Use your existing helper or adapt as needed
    desc, precautions, medications, diet, workout = helper(disease)
    # Flatten lists if needed
    if precautions and isinstance(precautions[0], list):
        precautions = precautions[0]
    if medications and isinstance(medications[0], list):
        medications = medications[0]
    if diet and isinstance(diet[0], list):
        diet = diet[0]
    if workout and isinstance(workout[0], list):
        workout = workout[0]
    return desc, precautions, medications, diet, workout

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    disease = request.form["disease"]
    description, precautions, medications, diet, workout = get_recommendations(disease)

    # Clean string-represented lists
    import ast
    if medications and isinstance(medications[0], str) and medications[0].startswith('['):
        medications = ast.literal_eval(medications[0])
    if diet and isinstance(diet[0], str) and diet[0].startswith('['):
        diet = ast.literal_eval(diet[0])
    if workout and isinstance(workout[0], str) and workout[0].startswith('['):
        workout = ast.literal_eval(workout[0])

    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="MediWise Disease Report", ln=True, align='C')
    pdf.ln(10)

    # Disease Name
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=f"Disease: {disease}", ln=True)
    pdf.ln(5)

    # Description
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Description:", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, txt=description)
    pdf.ln(5)

    # Medications
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Medications:", ln=True)
    pdf.set_font("Arial", '', 12)
    for med in medications:
        pdf.cell(0, 8, f"- {med}", ln=True)
    pdf.ln(5)

    # Precautions
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Precautions:", ln=True)
    pdf.set_font("Arial", '', 12)
    for pre in precautions:
        pdf.cell(0, 8, f"- {pre}", ln=True)
    pdf.ln(5)

    # Diet
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Recommended Diet:", ln=True)
    pdf.set_font("Arial", '', 12)
    for d in diet:
        pdf.cell(0, 8, f"- {d}", ln=True)
    pdf.ln(5)

    # Workout
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Recommended Workout:", ln=True)
    pdf.set_font("Arial", '', 12)
    for w in workout:
        pdf.cell(0, 8, f"- {w}", ln=True)
    pdf.ln(10)

    # Footer
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt="Generated by MediWise | www.mediwise.ai", ln=True, align='C')

    # Save the file
    os.makedirs('static', exist_ok=True)
    filename = f"{disease.replace(' ', '_')}_report.pdf"
    filepath = os.path.join('static', filename)
    abs_filepath = os.path.abspath(filepath)

    pdf.output(abs_filepath)
    return send_file(abs_filepath, as_attachment=True)

    # Now send the file
    return send_file(abs_filepath, as_attachment=True)

if __name__ == '__main__':

    app.run(debug=True)