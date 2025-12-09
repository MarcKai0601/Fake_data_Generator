#!/usr/bin/env python3
# sql_stream_loader.py
import gzip, sys, os, argparse, mysql.connector, time

def open_maybe_gzip(path):
    return gzip.open(path, 'rt', encoding='utf-8') if path.endswith('.gz') else open(path, 'r', encoding='utf-8')

def load_offset(p):
    try:
        with open(p, 'r') as f: return int(f.read().strip())
    except: return 0

def save_offset(p, n):
    if p:
        with open(p, 'w') as f: f.write(str(n))

def stream_execute(args):
    conn = mysql.connector.connect(
        host=args.host, port=args.port, user=args.user, password=args.password, database=args.database,
        autocommit=False
    )
    cur = conn.cursor()
    in_str = False; quote = ''
    in_line_c = False; in_block_c = False
    stmt = []
    processed = 0

    start_ts = time.time()
    last_milestone_ts = start_ts
    next_milestone = args.milestone_statements  # e.g. 100000

    with open(args.input, 'rb') as rb:
        # resume
        if args.progress and os.path.exists(args.progress):
            off = load_offset(args.progress)
            if off > 0: rb.seek(off)
        else:
            off = 0

        def read_char():
            nonlocal off
            c = rb.read(1)
            if not c: return None
            off += 1
            try:
                return c.decode('utf-8')
            except:
                # naive fallback (should not happen with your file)
                return c.decode('latin1')

        while True:
            c = read_char()
            if c is None: break

            if not in_str and not in_line_c and not in_block_c:
                if c == '-':
                    n = read_char()
                    if n == '--':
                        in_line_c = True
                        stmt.append(c); stmt.append(n)
                        continue
                    elif n is not None:
                        # unread one byte
                        off -= 1
                        rb.seek(off)
                elif c == '/':
                    n = read_char()
                    if n == '*':
                        in_block_c = True
                        stmt.append(c); stmt.append(n)
                        continue
                    elif n is not None:
                        off -= 1; rb.seek(off)
                elif c in ("'", '"'):
                    in_str = True; quote = c
            elif in_str:
                if c == quote:
                    # check escaped ''
                    n = read_char()
                    if n == quote:
                        stmt.append(c); stmt.append(n)
                        continue
                    elif n is not None:
                        off -= 1; rb.seek(off)
                        in_str = False; quote = ''
            elif in_line_c:
                if c == '\n': in_line_c = False
            elif in_block_c:
                if c == '*':
                    n = read_char()
                    if n == '/':
                        in_block_c = False
                        stmt.append(c); stmt.append(n)
                        continue
                    elif n is not None:
                        off -= 1; rb.seek(off)

            stmt.append(c)

            if not in_str and not in_line_c and not in_block_c and c == ';':
                sql = ''.join(stmt).strip()
                stmt = []
                if sql:
                    try:
                        cur.execute(sql)
                    except Exception as e:
                        print("SQL failed:", (sql[:220] + '...') if len(sql) > 220 else sql, file=sys.stderr)
                        if args.stop_on_error: raise
                    processed += 1

                    # 依 batch 提交
                    if processed % args.batch_statements == 0:
                        conn.commit()
                        if args.progress: save_offset(args.progress, off)

                    # 一般進度列印
                    if processed % args.print_progress_every == 0:
                        print(f"Processed {processed} statements, offset {off} bytes")

                    # ✅ 里程碑：每達到 milestone 筆，強制 commit 並印訊息
                    if processed >= next_milestone:
                        conn.commit()  # 確保 milestone 前的都已寫入
                        if args.progress: save_offset(args.progress, off)

                        now = time.time()
                        span = now - last_milestone_ts
                        total_span = now - start_ts
                        per_sec = args.milestone_statements / span if span > 0 else float('inf')
                        total_per_sec = processed / total_span if total_span > 0 else float('inf')

                        print(
                            f"✅ Milestone reached: {processed:,} statements committed | "
                            f"bytes={off:,} | "
                            f"chunk {args.milestone_statements:,} in {span:.2f}s ({per_sec:,.0f}/s) | "
                            f"total {total_span:.2f}s ({total_per_sec:,.0f}/s)"
                        )
                        last_milestone_ts = now
                        next_milestone += args.milestone_statements

        tail = ''.join(stmt).strip()
        if tail:
            try:
                cur.execute(tail)
            except Exception as e:
                print("SQL failed (tail):", (tail[:220] + '...') if len(tail) > 220 else tail, file=sys.stderr)
                if args.stop_on_error: raise
            processed += 1

        conn.commit()
        if args.progress: save_offset(args.progress, off)
        print(f"All done. statements: {processed:,}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help=".sql or .sql.gz")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--database", required=True)
    ap.add_argument("--batch-statements", type=int, default=50)
    ap.add_argument("--progress", default=None, help="progress file for resume")
    ap.add_argument("--print-progress-every", type=int, default=1000)
    ap.add_argument("--stop-on-error", action="store_true")
    ap.add_argument("--milestone-statements", type=int, default=100000, help="print & commit every N statements")
    args = ap.parse_args()
    stream_execute(args)
