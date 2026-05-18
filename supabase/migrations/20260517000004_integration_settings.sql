CREATE TABLE IF NOT EXISTS public.integration_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    procore_client_id TEXT,
    procore_client_secret TEXT,
    vision_ai_key TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS
ALTER TABLE public.integration_settings ENABLE ROW LEVEL SECURITY;

-- Allow read/write access (this might be too permissive, but we assume application handles auth)
CREATE POLICY "Allow authenticated full access to integration_settings" ON public.integration_settings
    FOR ALL
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
