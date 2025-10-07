-- ClickHouse init script: creates the table on first start
CREATE DATABASE IF NOT EXISTS default;

CREATE TABLE IF NOT EXISTS default.sensor_data (
    device_id String,
    ts        DateTime64(3),
    co        Float64,
    humidity  Float64,
    light     UInt8,
    lpg       Float64,
    motion    UInt8,
    smoke     Float64,
    temp      Float64
) ENGINE = MergeTree
ORDER BY (device_id, ts);