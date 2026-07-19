-- Run as travel_planning_migrator after every Alembic upgrade. This file grants only
-- runtime DML and forces RLS on V1 tables; it does not grant schema creation.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO travel_planning_api, travel_planning_worker, travel_planning_outbox;

DO $travel_planning_runtime_grants$
DECLARE
  relation_name text;
BEGIN
  FOR relation_name IN
    SELECT c.relname
      FROM pg_class AS c
      JOIN pg_namespace AS n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relkind IN ('r', 'p')
       AND c.relname LIKE 'v1\_%' ESCAPE '\'
  LOOP
    EXECUTE format('REVOKE ALL ON TABLE %I FROM PUBLIC', relation_name);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', relation_name);
    EXECUTE format(
      'GRANT SELECT, INSERT, UPDATE ON TABLE %I TO travel_planning_api, travel_planning_worker',
      relation_name
    );
  END LOOP;
END
$travel_planning_runtime_grants$;

-- A BYPASSRLS credential is acceptable only with this single-table grant. It
-- cannot read Trip, Run, Artifact, knowledge, or public-event content.
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM travel_planning_outbox;
GRANT SELECT, UPDATE ON TABLE v1_outbox_events TO travel_planning_outbox;

-- Public share routing is deliberately non-enumerable to runtime roles. The
-- API may register a newly-created opaque public ID, but tenant resolution is
-- possible only through the exact-match SECURITY DEFINER function.
REVOKE ALL ON TABLE travel_planning_share_public_lookup FROM
  travel_planning_api, travel_planning_worker, travel_planning_outbox;
GRANT INSERT ON TABLE travel_planning_share_public_lookup TO travel_planning_api;
REVOKE ALL ON TABLE v1_shares, v1_share_snapshots, v1_share_sessions,
  v1_share_idempotency_keys FROM travel_planning_worker;
GRANT DELETE ON TABLE v1_share_sessions TO travel_planning_api;
REVOKE ALL ON FUNCTION travel_planning_resolve_share_tenant(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION travel_planning_resolve_share_tenant(text) TO travel_planning_api;

DO $travel_planning_sequence_grants$
DECLARE
  sequence_name text;
BEGIN
  FOR sequence_name IN
    SELECT c.relname
      FROM pg_class AS c
      JOIN pg_namespace AS n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relkind = 'S'
       AND c.relname LIKE 'v1\_%' ESCAPE '\'
  LOOP
    EXECUTE format(
      'GRANT USAGE, SELECT ON SEQUENCE %I TO travel_planning_api, travel_planning_worker',
      sequence_name
    );
  END LOOP;
END
$travel_planning_sequence_grants$;
