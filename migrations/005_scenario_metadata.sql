-- Additive only; historical scenario fields and all research records stay intact.
ALTER TABLE training_scenarios ADD COLUMN training_context TEXT;
ALTER TABLE training_scenarios ADD COLUMN learning_objectives JSONB
    CHECK (learning_objectives IS NULL OR jsonb_typeof(learning_objectives) = 'array');
-- Shared key means mutually exclusive within a session; NULL means independent.
ALTER TABLE training_scenarios ADD COLUMN matched_pair_id TEXT
    CHECK (matched_pair_id IS NULL OR length(trim(matched_pair_id)) > 0);
-- Keep newly introduced content out of already-running older protocols.
ALTER TABLE training_scenarios ADD COLUMN introduced_in_version TEXT;
CREATE INDEX ON training_scenarios(matched_pair_id);
