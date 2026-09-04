-- ==========================================
-- MIGRATION: Tambah tabel projects + kolom project_id
-- Jalankan HANYA untuk database yang sudah berjalan.
-- Database baru cukup pakai create_tables.sql.
-- ==========================================

-- 1. Buat tabel projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    location VARCHAR(200),
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    last_opened_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);
CREATE INDEX IF NOT EXISTS idx_projects_last_opened_at ON projects(last_opened_at DESC);

-- 2. Tambah kolom project_id ke street_photos (nullable, data lama tetap valid)
ALTER TABLE street_photos ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);

CREATE INDEX IF NOT EXISTS idx_photos_project ON street_photos(project_id);
