-- ============================================================
-- UVIP Database Initialization
-- ============================================================
-- File ini dijalankan otomatis saat pertama kali container
-- PostgreSQL dibuat. Mengaktifkan extension PostGIS.
-- ============================================================

-- Enable PostGIS extension (untuk GeoAlchemy2 geometry columns)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify extension
SELECT PostGIS_Version();
