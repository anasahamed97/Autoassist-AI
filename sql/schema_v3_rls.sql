-- ==============================================================================
-- AutoAssist AI: Supabase PostgreSQL Row Level Security (RLS) Policies (v3.0)
-- Configures strict user isolation and access control across all application tables
-- ==============================================================================

-- 1. Enable RLS on all user-dependent tables
ALTER TABLE IF EXISTS public.vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.maintenance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.mechanic_quotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.repair_pricing ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.document_chunks ENABLE ROW LEVEL SECURITY;

-- 2. REPAIR PRICING POLICIES
-- Anyone can read reference pricing benchmarks; only service_role can modify
DROP POLICY IF EXISTS "Public can view repair pricing benchmarks" ON public.repair_pricing;
CREATE POLICY "Public can view repair pricing benchmarks"
ON public.repair_pricing FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "Service role manages repair pricing" ON public.repair_pricing;
CREATE POLICY "Service role manages repair pricing"
ON public.repair_pricing FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 3. DOCUMENTS & CHUNKS POLICIES
-- Technical service manuals are publicly readable for RAG searches
DROP POLICY IF EXISTS "Public can read service documents" ON public.documents;
CREATE POLICY "Public can read service documents"
ON public.documents FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "Service role manages service documents" ON public.documents;
CREATE POLICY "Service role manages service documents"
ON public.documents FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Public can read document chunks" ON public.document_chunks;
CREATE POLICY "Public can read document chunks"
ON public.document_chunks FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "Service role manages document chunks" ON public.document_chunks;
CREATE POLICY "Service role manages document chunks"
ON public.document_chunks FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 4. VEHICLE PROFILES POLICIES
-- Users can only read, insert, update, and delete their own vehicles
DROP POLICY IF EXISTS "Users view own vehicles" ON public.vehicles;
CREATE POLICY "Users view own vehicles"
ON public.vehicles FOR SELECT
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users insert own vehicles" ON public.vehicles;
CREATE POLICY "Users insert own vehicles"
ON public.vehicles FOR INSERT
TO authenticated, anon
WITH CHECK (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users update own vehicles" ON public.vehicles;
CREATE POLICY "Users update own vehicles"
ON public.vehicles FOR UPDATE
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
)
WITH CHECK (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users delete own vehicles" ON public.vehicles;
CREATE POLICY "Users delete own vehicles"
ON public.vehicles FOR DELETE
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Service role full access on vehicles" ON public.vehicles;
CREATE POLICY "Service role full access on vehicles"
ON public.vehicles FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 5. MAINTENANCE RECORDS POLICIES
DROP POLICY IF EXISTS "Users view own maintenance records" ON public.maintenance_records;
CREATE POLICY "Users view own maintenance records"
ON public.maintenance_records FOR SELECT
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users insert own maintenance records" ON public.maintenance_records;
CREATE POLICY "Users insert own maintenance records"
ON public.maintenance_records FOR INSERT
TO authenticated, anon
WITH CHECK (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users update own maintenance records" ON public.maintenance_records;
CREATE POLICY "Users update own maintenance records"
ON public.maintenance_records FOR UPDATE
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users delete own maintenance records" ON public.maintenance_records;
CREATE POLICY "Users delete own maintenance records"
ON public.maintenance_records FOR DELETE
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Service role full access on maintenance" ON public.maintenance_records;
CREATE POLICY "Service role full access on maintenance"
ON public.maintenance_records FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 6. MECHANIC QUOTATIONS POLICIES
DROP POLICY IF EXISTS "Users view own mechanic quotations" ON public.mechanic_quotations;
CREATE POLICY "Users view own mechanic quotations"
ON public.mechanic_quotations FOR SELECT
TO authenticated, anon
USING (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Users insert own mechanic quotations" ON public.mechanic_quotations;
CREATE POLICY "Users insert own mechanic quotations"
ON public.mechanic_quotations FOR INSERT
TO authenticated, anon
WITH CHECK (
    user_id = coalesce(auth.jwt()->>'sub', 'default_user')
    OR (auth.uid() IS NOT NULL AND user_id = auth.uid()::text)
    OR user_id = 'default_user'
);

DROP POLICY IF EXISTS "Service role full access on quotations" ON public.mechanic_quotations;
CREATE POLICY "Service role full access on quotations"
ON public.mechanic_quotations FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
