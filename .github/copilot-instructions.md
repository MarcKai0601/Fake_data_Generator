<!-- Auto-generated guidance for AI coding agents. Keep concise and actionable. -->
# Copilot / AI agent instructions for this repo

**Purpose:**
- Repo contains small Python tools to generate large gzipped SQL dump(s) and stream-load them into MySQL. Aim to help agents make safe, focused changes (features, bugfixes, performance tweaks).

**Big picture (why & flow):**
- `generate_fake_sql_1M.py` — creates gzipped SQL INSERT statements for table `g_paypay.t_order_http_log`. Typical usage: generate a large `.sql.gz` for load testing.
- `sql_stream_loader.py` — streams a `.sql` or `.sql.gz` file to MySQL by parsing SQL statements safely (handles strings, line/block comments) and commits in batches with resume support via a progress file.

**Key files to reference:**
- `generate_fake_sql_1M.py` — data ranges, generation patterns (accounts, merchants, payment methods, JSON payload shapes). Example: `mk_subreq(...)` and `mk_subresp(...)` implement different payment-method payloads.
- `sql_stream_loader.py` — char-by-char parser that tracks `in_str`, `in_line_c`, `in_block_c`. Resume via `--progress` file; batching controlled by `--batch-statements` and `--milestone-statements`.
- `fake_t_order_http_log_1M.sql` — sample output (if present) — use to validate parser assumptions (encoding, statement layout).

**Project-specific conventions / patterns:**
- Files may be gzipped; both generator and loader expect `.gz` suffix to choose gzip handling. Preserve `.gz` behaviour.
- The loader relies on a byte-offset resume mechanism: when writing progress, it stores the file offset (in bytes). When modifying parsing logic, preserve compatibility with existing offset files.
- SQL statements are written as large batched INSERTs. Generator uses a header + many rows per statement; loader executes statements sequentially and commits per `--batch-statements`.

**Common workflows / commands (examples):**
- Generate 10M rows (gzipped):
```
python3 generate_fake_sql_1M.py --out ./fake_t_order_http_log_10M.sql.gz --rows 10000000 --batch 1000
```
- Stream-load into MySQL with resume file and milestone reporting:
```
python3 sql_stream_loader.py --input ./fake_t_order_http_log_10M.sql.gz \
  --user root --password secret --database g_paypay \
  --progress ./load.progress --batch-statements 50 --milestone-statements 100000
```

**Testing & debugging tips:**
- Use small `--rows` / `--batch` when iterating on generator behavior.
- For loader changes, build a small `.sql` (or `.sql.gz`) with a handful of statements and run with `--stop-on-error` to surface parsing/SQL errors quickly.
- When investigating resume issues, inspect the `--progress` file (it's a plain integer offset).

**Integration / dependencies:**
- `sql_stream_loader.py` depends on `mysql-connector-python` (import `mysql.connector`). Ensure the runtime environment has this package installed.
- Scripts assume UTF-8 output; fallback decoding in loader uses latin1 only as a defensive measure.

**Safe-edit guidance for agents:**
- Preserve the byte-offset resume protocol and `.gz` suffix behaviour.
- If changing SQL parsing, add unit tests or a small sample `.sql` to validate edge-cases: nested quotes, `--` and `/* */` comments, and semicolons inside strings.
- Keep CLI flags and default semantics stable unless updating all callers/docs.

If anything here is unclear or you want a different level of detail (examples in zh-TW or more on testing), tell me which sections to expand.
