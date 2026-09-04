-- db/seed_entities.sql
-- The three v0 entities and the names each source uses for them.
-- Run by db/init.py. Safe to run more than once: INSERT OR IGNORE skips rows
-- whose primary key is already there, so nothing is overwritten.
--
-- Why this table exists with only three rows: so that feed number four maps
-- into it instead of inventing its own naming. Canonical IDs are the keys;
-- every name a source uses is an alias, and nothing ever joins on a name.

INSERT OR IGNORE INTO entity_registry
    (entity_id, entity_type, id_scheme, display_name, lat, lon, notes)
VALUES
    -- The chokepoint. Coordinates are the middle of the strait, good enough for
    -- a single marker on the Kepler.gl map.
    ('chokepoint:hormuz', 'chokepoint', 'PORTWATCH', 'Strait of Hormuz',
     26.5667, 56.2500,
     'IMF PortWatch portid=chokepoint6. Counts are modelled estimates from satellite AIS, not raw traffic.'),

    -- The country. No lat/lon: a country is not a point, and nothing in v0
    -- needs to draw one.
    ('country:USA', 'country', 'ISO3166A3', 'United States',
     NULL, NULL,
     'ISO 3166-1 alpha-3. Entity for the EIA weekly crude stocks series.'),

    -- The price benchmark. Not a place, so no coordinates.
    ('benchmark:brent', 'benchmark', 'INTERNAL', 'Brent crude',
     NULL, NULL,
     'Price benchmark, no physical location. OVX is attached here too per docs/feeds/fred.md, though CBOE computes it from WTI options.');

INSERT OR IGNORE INTO entity_alias (alias, scheme, entity_id) VALUES
    -- Strait of Hormuz
    ('chokepoint6',      'PORTWATCH', 'chokepoint:hormuz'),
    ('Strait of Hormuz', 'PORTWATCH', 'chokepoint:hormuz'),
    ('Hormuz',           'INTERNAL',  'chokepoint:hormuz'),

    -- United States
    ('USA',              'ISO3166A3', 'country:USA'),
    ('United States',    'EIA',       'country:USA'),
    ('US',               'INTERNAL',  'country:USA'),

    -- Brent
    ('Brent',            'INTERNAL',   'benchmark:brent'),
    ('DCOILBRENTEU',     'FRED',       'benchmark:brent'),
    ('OVXCLS',           'FRED',       'benchmark:brent');
