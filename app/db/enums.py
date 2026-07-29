import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SURVEYOR = "surveyor"
    PLANNER = "planner"
    OFFICER = "officer"

class MissionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PhotoSource(str, enum.Enum):
    MOBILE_LIVE = "mobile_live"
    MOBILE_UPLOAD = "mobile_upload"
    WEB_BATCH = "web_batch"

class ProcessingStatus(str, enum.Enum):
    QUEUED = "queued"
    MASKING = "masking"
    SEGMENTING = "segmenting"
    PREDICTING = "predicting"
    COMPLETED = "completed"
    FAILED = "failed"

class TargetIndicator(str, enum.Enum):
    BEAUTY = "beauty"
    SAFETY = "safety"
    COMFORT = "comfort"
    UVI = "uvi"

class SimulationIndicator(str, enum.Enum):
    UVI = "uvi"
    BEAUTY = "beauty"
    SAFETY = "safety"
    COMFORT = "comfort"
    GVI = "gvi"

class PolicyPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    RETRYING = "retrying"

class BatchJobStatus(str, enum.Enum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class ModelType(str, enum.Enum):
    PRIVACY_MASKING = "privacy_masking"
    SEGMENTATION = "segmentation"
    FEATURE_EXTRACTION = "feature_extraction"
    PERCEPTION_PREDICTION = "perception_prediction"