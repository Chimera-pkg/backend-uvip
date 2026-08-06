from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import PolicyRecommendation, User, SimulationSession
from app.schemas.policy_recommendation import PolicyRecommendationCreate, PolicyRecommendationResponse, PolicyRecommendationUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/policy-recommendations", tags=["Policy Recommendations"])

@router.post("/", response_model=PolicyRecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(data: PolicyRecommendationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    simulation_session = db.query(SimulationSession).filter(SimulationSession.id == data.session_id).first()
    if not simulation_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulasi Sesi dengan ID '{data.session_id}' tidak ditemukan."
        )

    recommendation = PolicyRecommendation(**data.model_dump())
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation

@router.get("/", response_model=List[PolicyRecommendationResponse])
def list_recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(PolicyRecommendation).all()

@router.get("/{recommendation_id}", response_model=PolicyRecommendationResponse)
def get_recommendation(recommendation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recommendation = db.query(PolicyRecommendation).filter(PolicyRecommendation.id == recommendation_id).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Rekomendasi kebijakan tidak ditemukan")
    return recommendation

@router.put("/{recommendation_id}", response_model=PolicyRecommendationResponse)
def update_recommendation(recommendation_id: UUID, data: PolicyRecommendationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recommendation = db.query(PolicyRecommendation).filter(PolicyRecommendation.id == recommendation_id).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Rekomendasi kebijakan tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(recommendation, key, val)
    db.commit()
    db.refresh(recommendation)
    return recommendation

@router.delete("/{recommendation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recommendation(recommendation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recommendation = db.query(PolicyRecommendation).filter(PolicyRecommendation.id == recommendation_id).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Rekomendasi kebijakan tidak ditemukan")
    db.delete(recommendation)
    db.commit()
    return None