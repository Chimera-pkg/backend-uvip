# UVIP — Urban Visual Perception API

Dokumentasi API + **contoh data** untuk backend UVIP (FastAPI).

- **Base URL (lokal):** `http://127.0.0.1:8000`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Auth:** JWT Bearer (`Authorization: Bearer <access_token>`)
- **Content-Type:** `application/json` untuk semua endpoint **kecuali** `POST /street-photos/` yang memakai `multipart/form-data`.

---

## Daftar Isi
1. [Autentikasi](#1-autentikasi)
2. [Users](#2-users)
3. [Corridors](#3-corridors)
4. [Survey Missions](#4-survey-missions)
5. [Mission Assignments](#5-mission-assignments)
6. [Street Photos](#6-street-photos)
7. [Segmentation Results](#7-segmentation-results)
8. [Perception Predictions](#8-perception-predictions)
9. [SHAP Values](#9-shap-values)
10. [Simulation Sessions](#10-simulation-sessions)
11. [Simulation Results](#11-simulation-results)
12. [Policy Recommendations](#12-policy-recommendations)
13. [Offline Sync Queue](#13-offline-sync-queue)
14. [Batch Upload Jobs](#14-batch-upload-jobs)
15. [Model Registries](#15-model-registries)
16. [Enum Reference](#enum-reference)
17. [Contoh Data Seed (Alur Lengkap)](#contoh-data-seed-alur-lengkap)

---

## Konvensi Umum

| Hal | Keterangan |
|---|---|
| Semua `id` | UUID v4 |
| Semua `created_at` | ISO-8601 dengan timezone (server yang mengisi) |
| Endpoint list `GET /...` | Mengembalikan array, tanpa pagination/query param |
| Endpoint `DELETE` | Sukses = `204 No Content` (body kosong) |
| Auth | Semua endpoint butuh Bearer token **kecuali** `POST /auth/register` & `POST /auth/login` |
| Error format | `{ "detail": "pesan error" }` |

Nilai koordinat memakai konteks **Kota Malang** (mis. lat `-7.9666420`, lng `112.6326000`).

---

## 1. Autentikasi

Prefix: `/auth` — tag: **Authentication**

| Method | Path | Auth | Deskripsi |
|---|---|---|---|
| POST | `/auth/register` | ❌ Public | Registrasi user baru |
| POST | `/auth/login` | ❌ Public | Login, mengembalikan JWT |

### POST /auth/register → `201 Created`
Request:
```json
{
  "name": "Andi Prasetyo",
  "email": "andi.surveyor@uvip.id",
  "password": "rahasia123",
  "role": "surveyor"
}
```
Response (`UserResponse`):
```json
{
  "id": "3f1a9c2e-7b44-4e21-9d33-2a1b6c5e8f01",
  "name": "Andi Prasetyo",
  "email": "andi.surveyor@uvip.id",
  "role": "surveyor",
  "is_active": true,
  "created_at": "2026-08-04T09:12:00+07:00"
}
```
Error: `400` → `{ "detail": "Email sudah terdaftar!" }`

### POST /auth/login → `200 OK`
Request:
```json
{
  "email": "andi.surveyor@uvip.id",
  "password": "rahasia123"
}
```
Response (`TokenResponse`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
Error:
- `401` → `{ "detail": "Email atau password salah!" }`
- `403` → `{ "detail": "Akun tidak aktif." }`

Gunakan token pada header berikutnya:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 2. Users

Prefix: `/users` — tag: **Users** — semua butuh auth.

| Method | Path | Body | Response | Catatan |
|---|---|---|---|---|
| GET | `/users/` | — | `List[UserResponse]` | |
| GET | `/users/{user_id}` | — | `UserResponse` | 404 jika tidak ada |
| PUT | `/users/{user_id}` | `UserUpdate` | `UserResponse` | |
| PATCH | `/users/{user_id}/activate` | — | `UserResponse` | **Admin only** (403), tidak boleh aktivasi diri sendiri (400) |

### PUT /users/{user_id}
Request (`UserUpdate`, semua opsional):
```json
{
  "name": "Andi Prasetyo, S.T.",
  "role": "planner",
  "is_active": true
}
```

### PATCH /users/{user_id}/activate
Errors:
- `403` → `{ "detail": "Hanya Admin yang dapat mengaktifkan akun." }`
- `400` → `{ "detail": "Admin tidak dapat mengaktifkan akunnya sendiri." }`
- `404` → `{ "detail": "User tidak ditemukan" }`

---

## 3. Corridors

Prefix: `/corridors` — tag: **Corridors** — semua butuh auth.

| Method | Path | Body | Response | Catatan |
|---|---|---|---|---|
| POST | `/corridors/` | `CorridorCreate` | `CorridorResponse` (201) | **Admin/Planner only** |
| GET | `/corridors/` | — | `List[CorridorResponse]` | |
| GET | `/corridors/{corridor_id}` | — | `CorridorResponse` | |
| PUT | `/corridors/{corridor_id}` | `CorridorUpdate` | `CorridorResponse` | |
| DELETE | `/corridors/{corridor_id}` | — | `204` | |

`geom` = WKT LINESTRING (SRID 4326), format `"lng lat, lng lat, ..."`.

### POST /corridors/ → `201`
Request (`CorridorCreate`):
```json
{
  "name": "Koridor Jalan Ijen",
  "city": "MALANG",
  "district": "Klojen",
  "length_km": 1.85,
  "description": "Koridor boulevard bersejarah dengan pepohonan palem.",
  "geom": "LINESTRING(112.6280 -7.9720, 112.6305 -7.9698, 112.6326 -7.9666)"
}
```
Response (`CorridorResponse`):
```json
{
  "id": "b2c4d6e8-1111-4a2b-8c3d-4e5f6a7b8c9d",
  "name": "Koridor Jalan Ijen",
  "city": "MALANG",
  "district": "Klojen",
  "length_km": 1.85,
  "description": "Koridor boulevard bersejarah dengan pepohonan palem.",
  "created_by": "3f1a9c2e-7b44-4e21-9d33-2a1b6c5e8f01",
  "created_at": "2026-08-04T09:20:00+07:00"
}
```
Error: `403` → `{ "detail": "Hanya Admin dan Planner yang dapat membuat koridor." }`

---

## 4. Survey Missions

Prefix: `/survey-missions` — tag: **Survey Missions** — semua butuh auth.

| Method | Path | Body | Response | Catatan |
|---|---|---|---|---|
| POST | `/survey-missions/` | `SurveyMissionCreate` | `SurveyMissionResponse` (201) | `created_by` diisi otomatis |
| GET | `/survey-missions/` | — | `List[SurveyMissionResponse]` | |
| GET | `/survey-missions/{mission_id}` | — | `SurveyMissionResponse` | |
| PUT | `/survey-missions/{mission_id}` | `SurveyMissionUpdate` | `SurveyMissionResponse` | |
| DELETE | `/survey-missions/{mission_id}` | — | `204` | |
| PATCH | `/survey-missions/{mission_id}/activate` | — | `SurveyMissionResponse` | 400 jika status sudah `completed` |
| PATCH | `/survey-missions/{mission_id}/complete` | — | `SurveyMissionResponse` | set `completed_at` |

### POST /survey-missions/ → `201`
Request (`SurveyMissionCreate`):
```json
{
  "name": "Survei Koridor Ijen Q3 2026",
  "description": "Pengambilan foto street-level sepanjang Jalan Ijen.",
  "corridor_id": "b2c4d6e8-1111-4a2b-8c3d-4e5f6a7b8c9d",
  "status": "active",
  "target_photo_count": 500,
  "started_at": "2026-08-05T07:00:00+07:00"
}
```
Response (`SurveyMissionResponse`):
```json
{
  "id": "c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e",
  "name": "Survei Koridor Ijen Q3 2026",
  "description": "Pengambilan foto street-level sepanjang Jalan Ijen.",
  "corridor_id": "b2c4d6e8-1111-4a2b-8c3d-4e5f6a7b8c9d",
  "created_by": "3f1a9c2e-7b44-4e21-9d33-2a1b6c5e8f01",
  "status": "active",
  "target_photo_count": 500,
  "started_at": "2026-08-05T07:00:00+07:00",
  "completed_at": null,
  "created_at": "2026-08-04T09:25:00+07:00"
}
```

---

## 5. Mission Assignments

Prefix: `/mission-assignments` — tag: **Mission Assignments** — semua butuh auth.

| Method | Path | Body | Response | Catatan |
|---|---|---|---|---|
| POST | `/mission-assignments/` | `MissionAssignmentCreate` | `MissionAssignmentResponse` (201) | **Admin/Planner only**; user harus role `surveyor` |
| GET | `/mission-assignments/` | — | `List[MissionAssignmentResponse]` | |
| GET | `/mission-assignments/{assignment_id}` | — | `MissionAssignmentResponse` | |
| PUT | `/mission-assignments/{assignment_id}` | `MissionAssignmentUpdate` | `MissionAssignmentResponse` | **kedua field wajib** |
| DELETE | `/mission-assignments/{assignment_id}` | — | `204` | |

### POST /mission-assignments/ → `201`
Request (`MissionAssignmentCreate`):
```json
{
  "mission_id": "c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e",
  "user_id": "3f1a9c2e-7b44-4e21-9d33-2a1b6c5e8f01"
}
```
Response (`MissionAssignmentResponse`):
```json
{
  "id": "d4e6f8a0-3333-4c4d-ae5f-6a7b8c9d0e1f",
  "mission_id": "c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e",
  "user_id": "3f1a9c2e-7b44-4e21-9d33-2a1b6c5e8f01",
  "assigned_at": "2026-08-04T09:30:00+07:00"
}
```
Errors:
- `403` → `{ "detail": "Hanya Admin dan Planner yang dapat menugaskan." }`
- `404` → `{ "detail": "Survey Mission tidak ditemukan" }` / `"User yang akan ditugaskan tidak ditemukan"`
- `400` → user bukan surveyor / assignment duplikat

---

## 6. Street Photos

Prefix: `/street-photos` — tag: **Street Photos** — semua butuh auth.
`POST` memakai **`multipart/form-data`** (upload file).

| Method | Path | Body | Response | Catatan |
|---|---|---|---|---|
| POST | `/street-photos/` | multipart form | `StreetPhotoResponse` (201) | server mengisi `file_path`, `file_size_kb`, `geom`, `uploaded_by`, `processing_status=queued` |
| GET | `/street-photos/` | — | `List[StreetPhotoResponse]` | |
| GET | `/street-photos/{photo_id}` | — | `StreetPhotoResponse` | |
| PUT | `/street-photos/{photo_id}` | `StreetPhotoUpdate` (JSON) | `StreetPhotoResponse` | |
| DELETE | `/street-photos/{photo_id}` | — | `204` | file fisik ikut dihapus |

### POST /street-photos/ (form fields)
| Field | Tipe | Wajib | Contoh |
|---|---|---|---|
| `file` | file | ✅ | `ijen_001.jpg` |
| `source` | enum `PhotoSource` | ✅ | `mobile_live` |
| `latitude` | float | ✅ | `-7.9666420` |
| `longitude` | float | ✅ | `112.6326000` |
| `captured_at` | datetime | ✅ | `2026-08-05T07:15:30+07:00` |
| `mission_id` | UUID | ❌ | `c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e` |
| `gps_accuracy_m` | float | ❌ | `4.5` |
| `compass_azimuth` | float | ❌ | `275.0` |
| `exif_timestamp` | datetime | ❌ | `2026-08-05T07:15:29+07:00` |
| `is_manual_capture` | bool | ❌ (default false) | `true` |
| `is_offline_sync` | bool | ❌ (default false) | `false` |

Contoh `curl`:
```bash
curl -X POST http://127.0.0.1:8000/street-photos/ \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@./ijen_001.jpg" \
  -F "source=mobile_live" \
  -F "latitude=-7.9666420" \
  -F "longitude=112.6326000" \
  -F "captured_at=2026-08-05T07:15:30+07:00" \
  -F "mission_id=c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e" \
  -F "gps_accuracy_m=4.5" \
  -F "compass_azimuth=275.0" \
  -F "is_manual_capture=true"
```
Response (`StreetPhotoResponse`):
```json
{
  "id": "e5f7a9b1-4444-4d5e-bf6a-7b8c9d0e1f20",
  "mission_id": "c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e",
  "uploaded_by": "3f1a9c2e-7b44-4e21-9d33-2a1b6c5e8f01",
  "source": "mobile_live",
  "original_filename": "ijen_001.jpg",
  "file_path": "uploads/photos/e5f7a9b1-4444-4d5e-bf6a-7b8c9d0e1f20.jpg",
  "file_size_kb": 2048,
  "latitude": -7.9666420,
  "longitude": 112.6326000,
  "gps_accuracy_m": 4.5,
  "compass_azimuth": 275.0,
  "exif_timestamp": null,
  "is_manual_capture": true,
  "is_offline_sync": false,
  "privacy_masked": false,
  "processing_status": "queued",
  "error_message": null,
  "captured_at": "2026-08-05T07:15:30+07:00",
  "created_at": "2026-08-05T07:16:00+07:00"
}
```

---

## 7. Segmentation Results

Prefix: `/segmentation-results` — tag: **Segmentation Results** — CRUD standar, semua butuh auth.
Path param: `{segmentation_id}`. **`photo_id` bersifat unik (1:1 dengan foto).**

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/segmentation-results/` | `SegmentationResultCreate` | `SegmentationResultResponse` (201) |
| GET | `/segmentation-results/` | — | `List[...]` |
| GET | `/segmentation-results/{segmentation_id}` | — | `...Response` |
| PUT | `/segmentation-results/{segmentation_id}` | `SegmentationResultUpdate` | `...Response` |
| DELETE | `/segmentation-results/{segmentation_id}` | — | `204` |

### POST /segmentation-results/ → `201`
Request (`SegmentationResultCreate`):
```json
{
  "photo_id": "e5f7a9b1-4444-4d5e-bf6a-7b8c9d0e1f20",
  "model_name": "SEGFORMER-B5",
  "vegetation_pct": 32.50,
  "building_pct": 21.10,
  "road_pct": 18.40,
  "sidewalk_pct": 9.30,
  "sky_pct": 12.70,
  "signage_pct": 1.20,
  "vehicle_pct": 3.10,
  "pedestrian_pct": 0.80,
  "street_furniture_pct": 0.90,
  "green_coverage_pct": 33.40,
  "building_coverage_pct": 21.10,
  "sky_visibility_pct": 12.70,
  "walkability_ratio": 0.7250,
  "visual_clutter_index": 0.3100,
  "mask_file_path": "uploads/masks/e5f7a9b1_mask.png",
  "inference_time_ms": 420
}
```
Response (`SegmentationResultResponse`): field yang sama + `id` & `created_at`.

---

## 8. Perception Predictions

Prefix: `/perception-predictions` — tag: **Perception Predictions** — CRUD standar, semua butuh auth.
Path param: `{prediction_id}`. **`photo_id` unik.**

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/perception-predictions/` | `PerceptionPredictionCreate` | `...Response` (201) |
| GET | `/perception-predictions/` | — | `List[...]` |
| GET | `/perception-predictions/{prediction_id}` | — | `...Response` |
| PUT | `/perception-predictions/{prediction_id}` | `PerceptionPredictionUpdate` | `...Response` |
| DELETE | `/perception-predictions/{prediction_id}` | — | `204` |

### POST /perception-predictions/ → `201`
Request (`PerceptionPredictionCreate`):
```json
{
  "photo_id": "e5f7a9b1-4444-4d5e-bf6a-7b8c9d0e1f20",
  "segmentation_id": "f6a8b0c2-5555-4e6f-c07b-8c9d0e1f2031",
  "model_version": "UVIP-XGB-v2.3",
  "beauty_score": 6.80,
  "safety_score": 7.20,
  "comfort_score": 6.50,
  "uvi_score": 6.83,
  "gvi_score": 33.40,
  "inference_time_ms": 55,
  "r2_reference": 0.812
}
```
Response: field yang sama + `id` & `created_at`.

---

## 9. SHAP Values

Prefix: `/shap-values` — tag: **SHAP Values** — CRUD standar, semua butuh auth.
Path param: `{shap_id}`.

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/shap-values/` | `ShapValueCreate` | `ShapValueResponse` (201) |
| GET | `/shap-values/` | — | `List[...]` |
| GET | `/shap-values/{shap_id}` | — | `...Response` |
| PUT | `/shap-values/{shap_id}` | `ShapValueUpdate` | `...Response` |
| DELETE | `/shap-values/{shap_id}` | — | `204` |

### POST /shap-values/ → `201`
Request (`ShapValueCreate`):
```json
{
  "prediction_id": "a7b9c1d3-6666-4f70-d18c-9d0e1f203142",
  "target_indicator": "uvi",
  "feature_name": "green_coverage_pct",
  "display_label": "Tutupan Hijau",
  "shap_value": 0.4120,
  "is_positive": true,
  "rank_order": 1
}
```
Response: field yang sama + `id` & `created_at`.

---

## 10. Simulation Sessions

Prefix: `/simulation-sessions` — tag: **Simulation Sessions** — CRUD standar, semua butuh auth.
Path param: `{session_id}`. `created_by` diisi otomatis.

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/simulation-sessions/` | `SimulationSessionCreate` | `...Response` (201) |
| GET | `/simulation-sessions/` | — | `List[...]` |
| GET | `/simulation-sessions/{session_id}` | — | `...Response` |
| PUT | `/simulation-sessions/{session_id}` | `SimulationSessionUpdate` | `...Response` |
| DELETE | `/simulation-sessions/{session_id}` | — | `204` |

### POST /simulation-sessions/ → `201`
Request (`SimulationSessionCreate`):
```json
{
  "corridor_id": "b2c4d6e8-1111-4a2b-8c3d-4e5f6a7b8c9d",
  "base_photo_id": "e5f7a9b1-4444-4d5e-bf6a-7b8c9d0e1f20",
  "base_prediction_id": "a7b9c1d3-6666-4f70-d18c-9d0e1f203142",
  "vegetation_adjustment_pct": 20.0,
  "sidewalk_width_adjustment_pct": 15.0,
  "signage_density_adjustment_pct": -10.0,
  "session_label": "Skenario Penghijauan Ijen +20%",
  "notes": "Simulasi menambah vegetasi & memperlebar trotoar."
}
```
Response: field yang sama + `id`, `created_by`, `created_at`.

---

## 11. Simulation Results

Prefix: `/simulation-results` — tag: **Simulation Results** — CRUD standar, semua butuh auth.
Path param: `{result_id}`.

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/simulation-results/` | `SimulationResultCreate` | `...Response` (201) |
| GET | `/simulation-results/` | — | `List[...]` |
| GET | `/simulation-results/{result_id}` | — | `...Response` |
| PUT | `/simulation-results/{result_id}` | `SimulationResultUpdate` | `...Response` |
| DELETE | `/simulation-results/{result_id}` | — | `204` |

### POST /simulation-results/ → `201`
Request (`SimulationResultCreate`):
```json
{
  "session_id": "b8c0d2e4-7777-4081-e29d-0e1f20314253",
  "indicator": "uvi",
  "score_before": 6.83,
  "score_after": 7.65,
  "score_delta": 0.82,
  "inference_time_ms": 48
}
```
Response: field yang sama + `id` & `created_at`.

---

## 12. Policy Recommendations

Prefix: `/policy-recommendations` — tag: **Policy Recommendations** — CRUD standar, semua butuh auth.
Path param: `{recommendation_id}`.

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/policy-recommendations/` | `PolicyRecommendationCreate` | `...Response` (201) |
| GET | `/policy-recommendations/` | — | `List[...]` |
| GET | `/policy-recommendations/{recommendation_id}` | — | `...Response` |
| PUT | `/policy-recommendations/{recommendation_id}` | `PolicyRecommendationUpdate` | `...Response` |
| DELETE | `/policy-recommendations/{recommendation_id}` | — | `204` |

### POST /policy-recommendations/ → `201`
Request (`PolicyRecommendationCreate`):
```json
{
  "session_id": "b8c0d2e4-7777-4081-e29d-0e1f20314253",
  "triggered_by": "uvi_score",
  "threshold_score": 5.00,
  "actual_score": 6.83,
  "recommendation_type": "penghijauan",
  "recommendation_text": "Tambah vegetasi peneduh di sisi timur koridor untuk menaikkan skor UVI.",
  "priority": "high",
  "is_auto_generated": true
}
```
Response: field yang sama + `id` & `created_at`.

---

## 13. Offline Sync Queue

Prefix: `/offline-sync-queues` — tag: **Offline Sync Queue** — CRUD standar, semua butuh auth.
Path param: `{queue_id}`. `user_id` diisi otomatis dari token.
*(Nama tabel DB: `offline_sync_queue`, singular.)*

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/offline-sync-queues/` | `OfflineSyncQueueCreate` | `...Response` (201) |
| GET | `/offline-sync-queues/` | — | `List[...]` |
| GET | `/offline-sync-queues/{queue_id}` | — | `...Response` |
| PUT | `/offline-sync-queues/{queue_id}` | `OfflineSyncQueueUpdate` | `...Response` |
| DELETE | `/offline-sync-queues/{queue_id}` | — | `204` |

### POST /offline-sync-queues/ → `201`
Request (`OfflineSyncQueueCreate`):
```json
{
  "device_id": "PIXEL-7A-SURVEYOR-01",
  "mission_id": "c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e",
  "local_file_path": "/sdcard/uvip/offline/img_20260805_0730.jpg",
  "latitude": -7.9701250,
  "longitude": 112.6298400,
  "gps_accuracy_m": 6.0,
  "compass_azimuth": 180.0,
  "is_manual_capture": false,
  "captured_at": "2026-08-05T07:30:00+07:00",
  "sync_status": "pending",
  "retry_count": 0
}
```
Response: field yang sama + `id`, `user_id`, `synced_photo_id`, `error_message`, `synced_at`, `last_retry_at`, `created_at`.

---

## 14. Batch Upload Jobs

Prefix: `/batch-upload-jobs` — tag: **Batch Upload Jobs** — CRUD standar, semua butuh auth.
Path param: `{job_id}`. `created_by` diisi otomatis.

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/batch-upload-jobs/` | `BatchUploadJobCreate` | `...Response` (201) |
| GET | `/batch-upload-jobs/` | — | `List[...]` |
| GET | `/batch-upload-jobs/{job_id}` | — | `...Response` |
| PUT | `/batch-upload-jobs/{job_id}` | `BatchUploadJobUpdate` | `...Response` |
| DELETE | `/batch-upload-jobs/{job_id}` | — | `204` |

### POST /batch-upload-jobs/ → `201`
Request (`BatchUploadJobCreate`):
```json
{
  "mission_id": "c3d5e7f9-2222-4b3c-9d4e-5f6a7b8c9d0e",
  "zip_filename": "ijen_batch_20260805.zip",
  "zip_file_path": "uploads/batches/ijen_batch_20260805.zip",
  "total_photos": 320,
  "processed_photos": 0,
  "failed_photos": 0,
  "status": "queued"
}
```
Response: field yang sama + `id`, `created_by`, `started_at`, `completed_at`, `error_log`, `created_at`.

---

## 15. Model Registries

Prefix: `/model-registries` — tag: **Model Registries** — CRUD standar, semua butuh auth.
Path param: `{model_id}`.
*(Nama tabel DB: `model_registry`, singular.)*

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/model-registries/` | `ModelRegistryCreate` | `...Response` (201) |
| GET | `/model-registries/` | — | `List[...]` |
| GET | `/model-registries/{model_id}` | — | `...Response` |
| PUT | `/model-registries/{model_id}` | `ModelRegistryUpdate` | `...Response` |
| DELETE | `/model-registries/{model_id}` | — | `204` |

### POST /model-registries/ → `201`
Request (`ModelRegistryCreate`):
```json
{
  "model_name": "UVIP Perception XGBoost",
  "model_type": "perception_prediction",
  "version_tag": "v2.3.0",
  "description": "Model prediksi persepsi visual multi-indikator.",
  "r2_score": 0.8120,
  "mae_score": 0.4500,
  "rmse_score": 0.6100,
  "training_dataset": "Malang Street View 2025 (12.400 foto)",
  "hardware_used": "NVIDIA RTX 4090",
  "is_active": true,
  "trained_at": "2026-07-20T10:00:00+07:00",
  "deployed_at": "2026-07-25T14:00:00+07:00"
}
```
Response: field yang sama + `id` & `created_at`.

---

## Enum Reference

| Enum | Dipakai di | Nilai |
|---|---|---|
| `UserRole` | user.role | `admin`, `surveyor`, `planner`, `officer` |
| `MissionStatus` | survey_missions.status | `active`, `paused`, `completed`, `cancelled` |
| `PhotoSource` | street_photos.source | `mobile_live`, `mobile_upload`, `web_batch` |
| `ProcessingStatus` | street_photos.processing_status | `queued`, `masking`, `segmenting`, `predicting`, `completed`, `failed` |
| `TargetIndicator` | shap_values.target_indicator | `beauty`, `safety`, `comfort`, `uvi` |
| `SimulationIndicator` | simulation_results.indicator | `uvi`, `beauty`, `safety`, `comfort`, `gvi` |
| `PolicyPriority` | policy_recommendations.priority | `high`, `medium`, `low` |
| `SyncStatus` | offline_sync_queue.sync_status | `pending`, `synced`, `failed`, `retrying` |
| `BatchJobStatus` | batch_upload_jobs.status | `queued`, `extracting`, `processing`, `completed`, `failed`, `partial` |
| `ModelType` | model_registry.model_type | `privacy_masking`, `segmentation`, `feature_extraction`, `perception_prediction` |

---

## Contoh Data Seed (Alur Lengkap)

Urutan ini menghormati semua foreign key — jalankan berurutan untuk mengisi data demo end-to-end.

| # | Endpoint | Data | Menghasilkan |
|---|---|---|---|
| 1 | `POST /auth/register` | admin (`role: admin`) | user admin |
| 2 | `POST /auth/register` | surveyor (`role: surveyor`) | user surveyor |
| 3 | `POST /auth/register` | planner (`role: planner`) | user planner |
| 4 | `POST /auth/login` | admin | `access_token` |
| 5 | `POST /corridors/` | Koridor Jalan Ijen | `corridor_id` |
| 6 | `POST /survey-missions/` | Survei Ijen Q3 | `mission_id` |
| 7 | `POST /mission-assignments/` | mission_id + surveyor_id | assignment |
| 8 | `POST /street-photos/` (multipart) | foto + GPS Ijen | `photo_id` |
| 9 | `POST /segmentation-results/` | photo_id + persentase kelas | `segmentation_id` |
| 10 | `POST /perception-predictions/` | photo_id + segmentation_id + skor | `prediction_id` |
| 11 | `POST /shap-values/` | prediction_id + fitur | shap value |
| 12 | `POST /simulation-sessions/` | corridor + base photo/prediction | `session_id` |
| 13 | `POST /simulation-results/` | session_id + skor before/after | result |
| 14 | `POST /policy-recommendations/` | session_id + rekomendasi | policy |
| 15 | `POST /model-registries/` | metadata model | model |

### Contoh 3 user awal
```json
[
  { "name": "Budi Santoso",   "email": "admin@uvip.id",    "password": "admin123",    "role": "admin" },
  { "name": "Andi Prasetyo",  "email": "surveyor@uvip.id", "password": "surveyor123", "role": "surveyor" },
  { "name": "Citra Dewi",     "email": "planner@uvip.id",  "password": "planner123",  "role": "planner" }
]
```

> **Catatan penting soal aktivasi akun:** user baru dibuat `is_active: true` secara default (lihat model), tetapi endpoint `PATCH /users/{id}/activate` hanya bisa dijalankan oleh **admin** dan admin **tidak boleh** mengaktifkan akunnya sendiri.

> **Catatan skema:** tabel `segmentation_results.photo_id` dan `perception_predictions.photo_id` bersifat **unik** — satu foto hanya boleh punya satu hasil segmentasi & satu prediksi.
