from flask import Flask, request, jsonify
import pandas as pd
import math

app = Flask(__name__)

# Load ideal crop nutrient values
ideal_df = pd.read_csv("crop_nutrient_ideal_values.csv")

# Fertilizer nutrient content & price (per 50 kg bag)
fertilizers = {
    "Urea": {"nutrient_fraction": 0.46, "bag_price": 268},
    "SSP": {"nutrient_fraction": 0.16, "bag_price": 362},
    "MOP": {"nutrient_fraction": 0.60, "bag_price": 900}
}

# Season data (approximate values)
season_conditions = {
    "Kharif": {"temperature": 30, "humidity": 80},
    "Rabi": {"temperature": 20, "humidity": 50},
    "Zaid": {"temperature": 35, "humidity": 60}
}

def recommend_fertilizer(crop, season, land_size, current_N, current_P, current_K):
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

    # Map nutrient → fertilizer
    if major_deficit == "N":
        fert_name = "Urea"
        fert_per_ha = deficits["N"] / fertilizers[fert_name]["nutrient_fraction"]
    elif major_deficit == "P":
        fert_name = "SSP"
        fert_per_ha = deficits["P"] / fertilizers[fert_name]["nutrient_fraction"]
    else:
        fert_name = "MOP"
        fert_per_ha = deficits["K"] / fertilizers[fert_name]["nutrient_fraction"]

    # Total fertilizer required for given land size
    total_fert = fert_per_ha * land_size

    # Bags required (50kg per bag, round up)
    bags_needed = math.ceil(total_fert / 50)

    # Total cost
    cost_per_bag = fertilizers[fert_name]["bag_price"]
    total_cost = bags_needed * cost_per_bag

    # Season details
    if season not in season_conditions:
        return {"error": f"Invalid season '{season}'. Choose from Kharif, Rabi, Zaid."}

    season_temp = season_conditions[season]["temperature"]
    season_humidity = season_conditions[season]["humidity"]

    return {
        "Crop": crop,
        "Season": season,
        "Land Size (ha)": land_size,
        "Ideal Temp (°C)": season_temp,
        "Ideal Humidity (%)": season_humidity,
        "Recommended Fertilizer": fert_name,
        "Amount per ha (kg)": round(fert_per_ha, 2),
        "Total Fertilizer (kg)": round(total_fert, 2),
        "Bags Required (50kg)": bags_needed,
        "Estimated Cost (Rs)": total_cost
    }

# API route
@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        crop = data["crop"]
        season = data["season"]
        land_size = float(data["land_size"])   # New input
        current_N = float(data["N"])
        current_P = float(data["P"])
        current_K = float(data["K"])

        result = recommend_fertilizer(crop, season, land_size, current_N, current_P, current_K)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
