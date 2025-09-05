from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load ideal crop nutrient values (from the CSV you generated earlier)
ideal_df = pd.read_csv("crop_nutrient_ideal_values.csv")

# Fertilizer nutrient content
fertilizers = {
    "Urea": 0.46,   # 46% N
    "SSP": 0.16,    # 16% P
    "MOP": 0.60     # 60% K
}

# Season data (approximate values)
season_conditions = {
    "Kharif": {"temperature": 30, "humidity": 80},
    "Rabi": {"temperature": 20, "humidity": 50},
    "Zaid": {"temperature": 35, "humidity": 60}
}

def recommend_fertilizer(crop, season, current_N, current_P, current_K):
    # Fetch ideal values for the crop
    row = ideal_df[ideal_df["Crop"].str.lower() == crop.lower()]
    if row.empty:
        return {"error": f"Crop '{crop}' not found in dataset."}
    
    row = row.iloc[0]
    ideal_N, ideal_P, ideal_K = row["N_mean"], row["P_mean"], row["K_mean"]

    # Calculate deficits
    deficits = {
        "N": max(0, ideal_N - current_N),
        "P": max(0, ideal_P - current_P),
        "K": max(0, ideal_K - current_K)
    }

    # If no deficit → no fertilizer needed
    if all(v == 0 for v in deficits.values()):
        return {"Crop": crop, "Message": "No fertilizer needed, soil nutrients are sufficient."}

    # Pick the nutrient with the highest deficit
    major_deficit = max(deficits, key=deficits.get)

    if major_deficit == "N":
        fert_name = "Urea"
        fert_needed = round(deficits["N"] / fertilizers["Urea"], 2)
    elif major_deficit == "P":
        fert_name = "SSP"
        fert_needed = round(deficits["P"] / fertilizers["SSP"], 2)
    else:
        fert_name = "MOP"
        fert_needed = round(deficits["K"] / fertilizers["MOP"], 2)

    # Season details
    if season not in season_conditions:
        return {"error": f"Invalid season '{season}'. Choose from Kharif, Rabi, Zaid."}

    season_temp = season_conditions[season]["temperature"]
    season_humidity = season_conditions[season]["humidity"]

    return {
        "Crop": crop,
        "Season": season,
        "Ideal Temp (°C)": season_temp,
        "Ideal Humidity (%)": season_humidity,
        "Recommended Fertilizer": fert_name,
        "Amount (kg/ha)": fert_needed
    }

# API route
@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        crop = data["crop"]
        season = data["season"]
        current_N = float(data["N"])
        current_P = float(data["P"])
        current_K = float(data["K"])

        result = recommend_fertilizer(crop, season, current_N, current_P, current_K)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
