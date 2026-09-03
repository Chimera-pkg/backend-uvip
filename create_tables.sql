
-- ==========================================
-- 0. EKSTENSI DATABASE
-- ==========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ==========================================
-- 1. ENUM TYPES
-- ==========================================
CREATE TYPE user_role AS ENUM ('admin', 'surveyor', 'planner', 'officer');
CREATE TYPE mission_status AS ENUM ('active', 'paused', 'completed', 'cancelled');
CREATE TYPE photo_source AS ENUM ('mobile_live', 'mobile_upload', 'web_batch');
CREATE TYPE processing_status AS ENUM ('queued', 'masking', 'segmenting', 'predicting', 'completed', 'failed');
CREATE TYPE target_indicator AS ENUM ('beauty', 'safety', 'comfort', 'uvi');
CREATE TYPE simulation_indicator AS ENUM ('uvi', 'beauty', 'safety', 'comfort', 'gvi');
CREATE TYPE policy_priority AS ENUM ('high', 'medium', 'low');
CREATE TYPE sync_status AS ENUM ('pending', 'synced', 'failed', 'retrying');
CREATE TYPE batch_job_status AS ENUM ('queued', 'extracting', 'processing', 'completed', 'failed', 'partial');
CREATE TYPE model_type AS ENUM ('privacy_masking', 'segmentation', 'feature_extraction', 'perception_prediction');

-- ==========================================
-- 2. TRIGGER FUNCTION UNTUK updated_at
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 3. TABEL 1: users
-- ==========================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 4. TABEL 2: corridors
-- ==========================================
CREATE TABLE corridors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    city VARCHAR(100) DEFAULT 'MALANG',
    district VARCHAR(100),
    geom GEOMETRY(LINESTRING, 4326),
    length_km DECIMAL(8, 3),
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_corridors_geom ON corridors USING GIST (geom);
CREATE INDEX idx_corridors_city ON corridors(city);

-- ==========================================
-- 5. TABEL 3: survey_missions
-- ==========================================
CREATE TABLE survey_missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    corridor_id UUID REFERENCES corridors(id),
    created_by UUID NOT NULL REFERENCES users(id),
    status mission_status DEFAULT 'active',
    target_photo_count INTEGER,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_missions_status ON survey_missions(status);
CREATE INDEX idx_missions_corridor ON survey_missions(corridor_id);

-- ==========================================
-- 6. TABEL 4: mission_assignments
-- ==========================================
CREATE TABLE mission_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES survey_missions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_mission_user UNIQUE (mission_id, user_id)
);

-- ==========================================
-- 7. TABEL 5: street_photos
-- ==========================================
CREATE TABLE street_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID REFERENCES survey_missions(id),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    source photo_source NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_size_kb INTEGER,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    geom GEOMETRY(POINT, 4326),
    gps_accuracy_m DECIMAL(6, 2),
    compass_azimuth DECIMAL(6, 2),
    exif_timestamp TIMESTAMPTZ,
    is_manual_capture BOOLEAN DEFAULT FALSE,
    is_offline_sync BOOLEAN DEFAULT FALSE,
    privacy_masked BOOLEAN DEFAULT FALSE,
    processing_status processing_status DEFAULT 'queued',
    error_message TEXT,
    captured_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_photos_geom ON street_photos USING GIST (geom);
CREATE INDEX idx_photos_mission ON street_photos(mission_id);
CREATE INDEX idx_photos_status ON street_photos(processing_status);
CREATE INDEX idx_photos_captured_at ON street_photos(captured_at DESC);
CREATE INDEX idx_photos_uploader ON street_photos(uploaded_by);

-- ==========================================
-- 8. TABEL 6: segmentation_results
-- ==========================================
CREATE TABLE segmentation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID UNIQUE REFERENCES street_photos(id),
    model_name VARCHAR(50) DEFAULT 'SEGFORMER-B5',
    
    vegetation_pct DECIMAL(5, 2),
    building_pct DECIMAL(5, 2),
    road_pct DECIMAL(5, 2),
    sidewalk_pct DECIMAL(5, 2),
    sky_pct DECIMAL(5, 2),
    signage_pct DECIMAL(5, 2),
    vehicle_pct DECIMAL(5, 2),
    pedestrian_pct DECIMAL(5, 2),
    street_furniture_pct DECIMAL(5, 2),
    
    green_coverage_pct DECIMAL(5, 2),
    building_coverage_pct DECIMAL(5, 2),
    sky_visibility_pct DECIMAL(5, 2),
    walkability_ratio DECIMAL(5, 4),
    visual_clutter_index DECIMAL(5, 4),
    
    mask_file_path VARCHAR(500),
    inference_time_ms INTEGER,
    seluruh_percentage DECIMAL(5, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_seg_photo_id ON segmentation_results(photo_id);

-- ==========================================
-- 9. TABEL 7: perception_predictions
-- ==========================================
CREATE TABLE perception_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID UNIQUE REFERENCES street_photos(id),
    segmentation_id UUID REFERENCES segmentation_results(id),
    model_version VARCHAR(50),
    beauty_score DECIMAL(4, 2),
    safety_score DECIMAL(4, 2),
    comfort_score DECIMAL(4, 2),
    uvi_score DECIMAL(4, 2),
    gvi_score DECIMAL(5, 2),
    inference_time_ms INTEGER,
    r2_reference DECIMAL(4, 3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_pred_photo_id ON perception_predictions(photo_id);
CREATE INDEX idx_pred_uvi ON perception_predictions(uvi_score);
CREATE INDEX idx_pred_created_at ON perception_predictions(created_at DESC);

-- ==========================================
-- 10. TABEL 8: shap_values
-- ==========================================
CREATE TABLE shap_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES perception_predictions(id),
    target_indicator target_indicator NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    display_label VARCHAR(200),
    shap_value DECIMAL(8, 4) NOT NULL,
    is_positive BOOLEAN,
    rank_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shap_prediction ON shap_values(prediction_id);
CREATE INDEX idx_shap_indicator ON shap_values(prediction_id, target_indicator);

-- ==========================================
-- 11. TABEL 9: simulation_sessions
-- ==========================================
CREATE TABLE simulation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID NOT NULL REFERENCES users(id),
    corridor_id UUID REFERENCES corridors(id),
    base_photo_id UUID REFERENCES street_photos(id),
    base_prediction_id UUID REFERENCES perception_predictions(id),
    
    vegetation_adjustment_pct DECIMAL(5, 2) DEFAULT 0,
    sidewalk_width_adjustment_pct DECIMAL(5, 2) DEFAULT 0,
    signage_density_adjustment_pct DECIMAL(5, 2) DEFAULT 0,
    
    session_label VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sim_sessions_user ON simulation_sessions(created_by);
CREATE INDEX idx_sim_sessions_corridor ON simulation_sessions(corridor_id);

-- ==========================================
-- 12. TABEL 10: simulation_results
-- ==========================================
CREATE TABLE simulation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES simulation_sessions(id),
    indicator simulation_indicator NOT NULL,
    score_before DECIMAL(4, 2) NOT NULL,
    score_after DECIMAL(4, 2) NOT NULL,
    score_delta DECIMAL(5, 2),
    inference_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sim_results_session ON simulation_results(session_id);
CREATE INDEX idx_sim_results_indicator ON simulation_results(session_id, indicator);

-- ==========================================
-- 13. TABEL 11: policy_recommendations
-- ==========================================
CREATE TABLE policy_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES simulation_sessions(id),
    triggered_by VARCHAR(20) NOT NULL,
    threshold_score DECIMAL(4, 2) DEFAULT 5.00,
    actual_score DECIMAL(4, 2),
    recommendation_type VARCHAR(50),
    recommendation_text TEXT NOT NULL,
    priority policy_priority DEFAULT 'medium',
    is_auto_generated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 14. TABEL 12: offline_sync_queue
-- ==========================================
CREATE TABLE offline_sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    mission_id UUID REFERENCES survey_missions(id),
    local_file_path VARCHAR(500),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    gps_accuracy_m DECIMAL(6, 2),
    compass_azimuth DECIMAL(6, 2),
    is_manual_capture BOOLEAN DEFAULT FALSE,
    captured_at TIMESTAMPTZ NOT NULL,
    sync_status sync_status DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMPTZ,
    synced_photo_id UUID REFERENCES street_photos(id),
    error_message TEXT,
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_offline_device ON offline_sync_queue(device_id);
CREATE INDEX idx_offline_status ON offline_sync_queue(sync_status);
CREATE INDEX idx_offline_user ON offline_sync_queue(user_id);

-- ==========================================
-- 15. TABEL 13: batch_upload_jobs
-- ==========================================
CREATE TABLE batch_upload_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID REFERENCES users(id),
    mission_id UUID REFERENCES survey_missions(id),
    zip_filename VARCHAR(255),
    zip_file_path VARCHAR(500),
    total_photos INTEGER DEFAULT 0,
    processed_photos INTEGER DEFAULT 0,
    failed_photos INTEGER DEFAULT 0,
    status batch_job_status DEFAULT 'queued',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_batch_status ON batch_upload_jobs(status);
CREATE INDEX idx_batch_created_by ON batch_upload_jobs(created_by);

-- ==========================================
-- 16. TABEL 14: model_registry
-- ==========================================
CREATE TABLE model_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_type model_type NOT NULL,
    version_tag VARCHAR(50),
    description TEXT,
    r2_score DECIMAL(5, 4),
    mae_score DECIMAL(8, 4),
    rmse_score DECIMAL(8, 4),
    training_dataset TEXT,
    hardware_used VARCHAR(100),
    is_active BOOLEAN DEFAULT FALSE,
    trained_at TIMESTAMPTZ,
    deployed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_model_name ON model_registry(model_name);
CREATE UNIQUE INDEX idx_model_type_active ON model_registry(model_type) WHERE is_active = TRUE;