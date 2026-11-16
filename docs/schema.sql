-- LaundryMann 2.0 : PostgreSQL 16 schema (reference DDL; Alembic is the source of truth in code)
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email citext NOT NULL UNIQUE,
  password_hash text NOT NULL,
  display_name text NOT NULL CHECK (length(display_name) BETWEEN 1 AND 80),
  role text NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
  share_for_training boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE TABLE refresh_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  family_id uuid NOT NULL,
  token_hash bytea NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  replaced_by uuid REFERENCES refresh_tokens(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_refresh_family ON refresh_tokens(family_id);

CREATE TABLE model_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL CHECK (name IN ('garment_det','stain_det','fabric_cls','label_det','symbol_cls')),
  version text NOT NULL,
  sha256 text NOT NULL,
  metrics jsonb NOT NULL DEFAULT '{}',
  licence_note text,
  is_active boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, version)
);
CREATE UNIQUE INDEX ux_model_active ON model_versions(name) WHERE is_active;

CREATE TABLE rule_sets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version text NOT NULL UNIQUE,
  sha256 text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE images (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind text NOT NULL CHECK (kind IN ('garment','basket','label')),
  storage_key text NOT NULL UNIQUE,
  sha256 text NOT NULL,
  width int NOT NULL CHECK (width > 0),
  height int NOT NULL CHECK (height > 0),
  blur_score real,
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (owner_id, sha256)
);
CREATE INDEX ix_images_owner_exp ON images(owner_id, expires_at);

CREATE TABLE analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  image_id uuid REFERENCES images(id) ON DELETE SET NULL,
  garment_category text,
  colour_family text CHECK (colour_family IN ('white','light','pastel','bright','dark','multi')),
  bleed_risk text CHECK (bleed_risk IN ('receiver','low','high')),
  palette jsonb,
  fabric_value text CHECK (fabric_value IN ('cotton','linen','silk','wool','synthetic','denim','other','unknown')),
  fabric_conf real CHECK (fabric_conf BETWEEN 0 AND 1),
  fabric_source text CHECK (fabric_source IN ('model','ocr','user')),
  plan jsonb NOT NULL,
  reasons jsonb NOT NULL DEFAULT '[]',
  warnings jsonb NOT NULL DEFAULT '[]',
  abstained boolean NOT NULL DEFAULT false,
  detector_mv uuid REFERENCES model_versions(id),
  fabric_mv uuid REFERENCES model_versions(id),
  stain_mv uuid REFERENCES model_versions(id),
  rule_set_id uuid REFERENCES rule_sets(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_analyses_owner_created ON analyses(owner_id, created_at DESC);

CREATE TABLE stain_detections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  bbox real[4] NOT NULL,
  score real NOT NULL CHECK (score BETWEEN 0 AND 1),
  area_pct real CHECK (area_pct BETWEEN 0 AND 100),
  stain_type text CHECK (stain_type IN ('oil','tea_coffee','food_curry','ink','blood_protein','mud','rust','other')),
  type_source text CHECK (type_source IN ('user','model'))
);

CREATE TABLE care_label_reads (
  analysis_id uuid PRIMARY KEY REFERENCES analyses(id) ON DELETE CASCADE,
  raw_text text,
  constraints jsonb NOT NULL,
  symbols jsonb NOT NULL DEFAULT '[]',
  source_conf jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE corrections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  attribute text NOT NULL,
  old_value text,
  new_value text NOT NULL,
  status text NOT NULL DEFAULT 'quarantined' CHECK (status IN ('quarantined','approved','rejected')),
  share_ok boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_corrections_status ON corrections(status, created_at);

CREATE TABLE wardrobe_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name text NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
  latest_analysis_id uuid REFERENCES analyses(id) ON DELETE SET NULL,
  notes text,
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_wardrobe_active ON wardrobe_items(owner_id) WHERE archived_at IS NULL;

CREATE TABLE load_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  capacity_items int NOT NULL CHECK (capacity_items BETWEEN 1 AND 60),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE load_plan_loads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  load_plan_id uuid NOT NULL REFERENCES load_plans(id) ON DELETE CASCADE,
  position int NOT NULL,
  shared_params jsonb NOT NULL,
  explanation text NOT NULL
);
CREATE TABLE load_plan_items (
  load_id uuid NOT NULL REFERENCES load_plan_loads(id) ON DELETE CASCADE,
  analysis_id uuid NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  PRIMARY KEY (load_id, analysis_id)
);

CREATE TABLE audit_log (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  event text NOT NULL,
  ip_hash text,
  meta jsonb NOT NULL DEFAULT '{}',
  ts timestamptz NOT NULL DEFAULT now()
);

-- Optional defence in depth: Row-Level Security example
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY analyses_owner ON analyses USING (owner_id = current_setting('app.user_id')::uuid);
