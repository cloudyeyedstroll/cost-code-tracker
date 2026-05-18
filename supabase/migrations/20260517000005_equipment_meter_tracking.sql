-- Migration: Add equipment meter tracking fields
ALTER TABLE public.equipment_logs
ADD COLUMN start_meter NUMERIC,
ADD COLUMN end_meter NUMERIC,
ADD COLUMN calculated_runtime NUMERIC;
