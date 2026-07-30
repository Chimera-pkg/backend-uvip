import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import (
    auth, users, corridors, survey_missions, mission_assignments,
    street_photos, segmentation_results, perception_predictions,
    shap_values, simulation_sessions, simulation_results,
    policy_recommendations, offline_sync_queues, batch_upload_jobs,
    model_registries
)

app = FastAPI(
    title="UVIP - Urban Visual Perception API",
    version="1.0.0"
)

# Buat folder uploads jika belum ada
os.makedirs("uploads/photos", exist_ok=True)

# Mount folder static uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# registrasi router auth (1 public endpoint)
app.include_router(auth.router)

# registrasi router fitur terproteksi
app.include_router(users.router)
app.include_router(corridors.router)
app.include_router(survey_missions.router)
app.include_router(mission_assignments.router)
app.include_router(street_photos.router)
app.include_router(segmentation_results.router)
app.include_router(perception_predictions.router)
app.include_router(shap_values.router)
app.include_router(simulation_sessions.router)
app.include_router(simulation_results.router)
app.include_router(policy_recommendations.router)
app.include_router(offline_sync_queues.router)
app.include_router(batch_upload_jobs.router)
app.include_router(model_registries.router)

@app.get("/")
def root():
    return {"message": "UVIP API Online"}