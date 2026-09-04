import uuid
from sqlalchemy import (
    Column, String, Boolean, Integer, Numeric, Text, DateTime,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from geoalchemy2 import Geometry
from app.db.database import Base
from app.db.enums import *

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # role = Column(ENUM(UserRole, name="user_role", create_type=False), nullable=False)
    role = Column(
        ENUM(
            UserRole, 
            name="user_role", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        nullable=False
    )
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Corridor(Base):
    __tablename__ = "corridors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    city = Column(String(100), default="MALANG")
    district = Column(String(100))
    geom = Column(Geometry("LINESTRING", srid=4326))
    length_km = Column(Numeric(8, 3))
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SurveyMission(Base):
    __tablename__ = "survey_missions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    corridor_id = Column(UUID(as_uuid=True), ForeignKey("corridors.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # status = Column(ENUM(MissionStatus, name="mission_status", create_type=False), default=MissionStatus.ACTIVE)
    status = Column(
        ENUM(
            MissionStatus, 
            name="mission_status", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        default=MissionStatus.ACTIVE
    )
    target_photo_count = Column(Integer)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MissionAssignment(Base):
    __tablename__ = "mission_assignments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("survey_missions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("mission_id", "user_id", name="unique_mission_user"),)

class StreetPhoto(Base):
    __tablename__ = "street_photos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("survey_missions.id"))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # source = Column(ENUM(PhotoSource, name="photo_source", create_type=False), nullable=False)
    source = Column(
        ENUM(
            PhotoSource, 
            name="photo_source", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        nullable=False
    )
    original_filename = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_size_kb = Column(Integer)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    street_name = Column(String(255))
    geom = Column(Geometry("POINT", srid=4326))
    gps_accuracy_m = Column(Numeric(6, 2))
    compass_azimuth = Column(Numeric(6, 2))
    exif_timestamp = Column(DateTime(timezone=True))
    is_manual_capture = Column(Boolean, default=False)
    is_offline_sync = Column(Boolean, default=False)
    privacy_masked = Column(Boolean, default=False)
    # processing_status = Column(ENUM(ProcessingStatus, name="processing_status", create_type=False), default=ProcessingStatus.QUEUED)
    processing_status = Column(
        ENUM(
            ProcessingStatus, 
            name="processing_status", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        default=ProcessingStatus.QUEUED
    )
    error_message = Column(Text)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SegmentationResult(Base):
    __tablename__ = "segmentation_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("street_photos.id"), unique=True)
    model_name = Column(String(50), default="SEGFORMER-B5")
    vegetation_pct = Column(Numeric(5, 2))
    building_pct = Column(Numeric(5, 2))
    road_pct = Column(Numeric(5, 2))
    sidewalk_pct = Column(Numeric(5, 2))
    sky_pct = Column(Numeric(5, 2))
    signage_pct = Column(Numeric(5, 2))
    vehicle_pct = Column(Numeric(5, 2))
    pedestrian_pct = Column(Numeric(5, 2))
    street_furniture_pct = Column(Numeric(5, 2))
    green_coverage_pct = Column(Numeric(5, 2))
    building_coverage_pct = Column(Numeric(5, 2))
    sky_visibility_pct = Column(Numeric(5, 2))
    walkability_ratio = Column(Numeric(5, 4))
    visual_clutter_index = Column(Numeric(5, 4))
    mask_file_path = Column(String(500))
    segmentation_url = Column(String(500))
    privacy_masked_url = Column(String(500))
    segmentation_overlay_url = Column(String(500))
    inference_time_ms = Column(Integer)
    seluruh_percentage = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PerceptionPrediction(Base):
    __tablename__ = "perception_predictions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("street_photos.id"), unique=True)
    segmentation_id = Column(UUID(as_uuid=True), ForeignKey("segmentation_results.id"))
    model_version = Column(String(50))
    beauty_score = Column(Numeric(4, 2))
    safety_score = Column(Numeric(4, 2))
    comfort_score = Column(Numeric(4, 2))
    uvi_score = Column(Numeric(4, 2))
    gvi_score = Column(Numeric(5, 2))
    inference_time_ms = Column(Integer)
    r2_reference = Column(Numeric(4, 3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ShapValue(Base):
    __tablename__ = "shap_values"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("perception_predictions.id"), nullable=False)
    # target_indicator = Column(ENUM(TargetIndicator, name="target_indicator", create_type=False), nullable=False)
    target_indicator = Column(
        ENUM(
            TargetIndicator, 
            name="target_indicator", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        nullable=False
    )
    feature_name = Column(String(100), nullable=False)
    display_label = Column(String(200))
    shap_value = Column(Numeric(8, 4), nullable=False)
    is_positive = Column(Boolean)
    rank_order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SimulationSession(Base):
    __tablename__ = "simulation_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    corridor_id = Column(UUID(as_uuid=True), ForeignKey("corridors.id"))
    base_photo_id = Column(UUID(as_uuid=True), ForeignKey("street_photos.id"))
    base_prediction_id = Column(UUID(as_uuid=True), ForeignKey("perception_predictions.id"))
    vegetation_adjustment_pct = Column(Numeric(5, 2), default=0)
    sidewalk_width_adjustment_pct = Column(Numeric(5, 2), default=0)
    signage_density_adjustment_pct = Column(Numeric(5, 2), default=0)
    session_label = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SimulationResult(Base):
    __tablename__ = "simulation_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("simulation_sessions.id"), nullable=False)
    # indicator = Column(ENUM(SimulationIndicator, name="simulation_indicator", create_type=False), nullable=False)
    indicator = Column(
        ENUM(
            SimulationIndicator, 
            name="simulation_indicator", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        nullable=False
    )
    score_before = Column(Numeric(4, 2), nullable=False)
    score_after = Column(Numeric(4, 2), nullable=False)
    score_delta = Column(Numeric(5, 2))
    inference_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PolicyRecommendation(Base):
    __tablename__ = "policy_recommendations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("simulation_sessions.id"))
    triggered_by = Column(String(20), nullable=False)
    threshold_score = Column(Numeric(4, 2), default=5.00)
    actual_score = Column(Numeric(4, 2))
    recommendation_type = Column(String(50))
    recommendation_text = Column(Text, nullable=False)
    # priority = Column(ENUM(PolicyPriority, name="policy_priority", create_type=False), default=PolicyPriority.MEDIUM)
    priority = Column(
        ENUM(
            PolicyPriority, 
            name="policy_priority", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        default=PolicyPriority.MEDIUM
    )
    is_auto_generated = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OfflineSyncQueue(Base):
    __tablename__ = "offline_sync_queue"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    mission_id = Column(UUID(as_uuid=True), ForeignKey("survey_missions.id"))
    local_file_path = Column(String(500))
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    gps_accuracy_m = Column(Numeric(6, 2))
    compass_azimuth = Column(Numeric(6, 2))
    is_manual_capture = Column(Boolean, default=False)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    # sync_status = Column(ENUM(SyncStatus, name="sync_status", create_type=False), default=SyncStatus.PENDING)
    sync_status = Column(
        ENUM(
            SyncStatus, 
            name="sync_status", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        default=SyncStatus.PENDING
    )
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime(timezone=True))
    synced_photo_id = Column(UUID(as_uuid=True), ForeignKey("street_photos.id"))
    error_message = Column(Text)
    synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BatchUploadJob(Base):
    __tablename__ = "batch_upload_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    mission_id = Column(UUID(as_uuid=True), ForeignKey("survey_missions.id"))
    zip_filename = Column(String(255))
    zip_file_path = Column(String(500))
    total_photos = Column(Integer, default=0)
    processed_photos = Column(Integer, default=0)
    failed_photos = Column(Integer, default=0)
    # status = Column(ENUM(BatchJobStatus, name="batch_job_status", create_type=False), default=BatchJobStatus.QUEUED)
    status = Column(
        ENUM(
            BatchJobStatus, 
            name="batch_job_status", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        default=BatchJobStatus.QUEUED
    )
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_log = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    # model_type = Column(ENUM(ModelType, name="model_type", create_type=False), nullable=False)
    model_type = Column(
        ENUM(
            ModelType, 
            name="model_type", 
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj]
        ), 
        nullable=False
    )
    version_tag = Column(String(50))
    description = Column(Text)
    r2_score = Column(Numeric(5, 4))
    mae_score = Column(Numeric(8, 4))
    rmse_score = Column(Numeric(8, 4))
    training_dataset = Column(Text)
    hardware_used = Column(String(100))
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime(timezone=True))
    deployed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VideoOutputSegmentation(Base):
    __tablename__ = "video_output_segmentations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("street_photos.id"), unique=True)
    video_url = Column(String(500), nullable=False)
    fps = Column(Numeric(5, 2), default=0)
    frame_count = Column(Numeric(5, 2), default=0)
    width = Column(Numeric(5, 2), default=0)
    height = Column(Numeric(5, 2), default=0)
    duration_seconds = Column(Numeric(5, 2), default=0)
    frames_processed = Column(Numeric(5, 2), default=0)
    processing_time_ms = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())