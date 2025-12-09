# #!/usr/bin/env python3
# """
# Generate fake SQL INSERTs for g_paypay.t_order_http_log

# Usage:
#     python3 generate_fake_sql_1M.py --out ./fake_t_order_http_log_1M.sql.gz --rows 1000000 --batch 1000

# Notes:
# - The script writes a gzipped SQL file.
# - Adjust --rows and --batch if you want fewer/more rows or different batch-size.
# """
# import argparse, gzip, json, random
# from datetime import datetime, timedelta

# def make_generator(num_rows=1000000, batch_size=1000, out_path="fake_t_order_http_log_1M.sql.gz"):
#     start_dt = datetime(2018,1,1,0,0,0)
#     end_dt = datetime(2025,11,4,23,59,59)
#     total_seconds = int((end_dt - start_dt).total_seconds())

#     account_ids = [949, 1027, 1244, 1500, 2001, 3050, 4123, 587, 678, 1111]
#     merchant_codes = ["587678", "24h497449", "15705852", "A1001", "B2002", "C3003"]
#     emails = ["user{}@example.com".format(i) for i in range(1,51)]
#     names = ["Name{}".format(i) for i in range(1,51)]
#     payment_methods = ["QRIS", "bank_qr", "momo_bank", "QUICK.BANKVA", "ALIPAY", "GCASH"]
#     statuses = ["PROCESSING", "SUCCESS", "FAILED", "PENDING"]

#     def rand_dt_iso():
#         dt = start_dt + timedelta(seconds=random.randint(0, total_seconds))
#         return dt.strftime("%Y-%m-%d %H:%M:%S")

#     def esc(s):
#         if s is None:
#             return "NULL"
#         return "'" + s.replace("'", "''") + "'"

#     def mk_subreq(order_id, merchant, method, amount):
#         if method == "QRIS":
#             obj = {
#                 "amount": str(amount),
#                 "customer": {"email": random.choice(emails), "name": random.choice(names), "phone": str(random.randint(8000000000, 8999999999))},
#                 "merchantCode": merchant,
#                 "merchantNotifyUrl": f"https://gpay.dfgame.club/notify/{merchant}",
#                 "merchantOrderId": order_id,
#                 "paymentMethodCode": method
#             }
#         elif method == "bank_qr":
#             obj = {"merchantNo": f"{random.randint(100000,999999)}", "outTradeNo": order_id, "type": "bank_qr", "code": "bank_qr", "amount": str(amount), "timestamp": random.randint(1500000000, 1762227644), "notifyUrl": "https://gpay.dfgame.club/notify/24hpay", "sign": "%032x" % random.getrandbits(128)}
#         elif method == "momo_bank":
#             obj = {"merchantNo": f"{random.randint(100000,999999)}", "outTradeNo": order_id, "type": "momo_bank", "code": "momo_bank", "amount": str(amount), "timestamp": random.randint(1500000000, 1762227644), "notifyUrl": "https://gpay.dfgame.club/notify/24hpay", "sign": "%032x" % random.getrandbits(128)}
#         else:
#             obj = {"out_trade_no": order_id, "total_fee": str(amount), "trade_type": method, "notify_url": "https://gpay.dfgame.club/notify/xnetpay", "mch_id": str(random.randint(15000000,15999999))}
#         return json.dumps(obj, ensure_ascii=False)

#     def mk_subresp(order_id, merchant, method, amount):
#         if method == "QRIS":
#             resp = {"code": 200, "msg":"success", "data":{"merchantCode": merchant, "merchantOrderId": order_id, "amount": f"{amount}.00", "status": random.choice(statuses), "paymentMethodCode": method}}
#         elif method in ("bank_qr","momo_bank"):
#             resp = {"code":"200", "data": f"https://pay.example.com/{method}.html?{random.getrandbits(160):x}", "success": True, "message": "success"}
#         else:
#             resp = {"order_no": f"S{random.randint(1000000000,9999999999)}", "out_trade_no": order_id, "total_fee": str(amount), "return_msg":"SUCCESS", "return_code":"SUCCESS"}
#         return json.dumps(resp, ensure_ascii=False)

#     header = "INSERT INTO g_paypay.t_order_http_log (OrderId,`Type`,AccountId,SubmitRequest,SubmitResponse,SubmitTime,QueryRequest,QueryResponse,QueryTime,CallbackRequest,CallbackTime) VALUES\n"

#     written = 0
#     with gzip.open(out_path, "wt", encoding="utf-8") as f:
#         while written < num_rows:
#             rows = []
#             take = min(batch_size, num_rows - written)
#             for i in range(take):
#                 order_dt = start_dt + timedelta(seconds=random.randint(0, total_seconds))
#                 order_id = "PAY" + order_dt.strftime("%Y%m%d%H%M%S") + f"{random.randint(100000,999999)}"
#                 acct = random.choice(account_ids)
#                 merchant = random.choice(merchant_codes)
#                 method = random.choice(payment_methods)
#                 amount = random.choice([10000,50000,70000,500000,700000,1000000])
#                 sr = mk_subreq(order_id, merchant, method, amount)
#                 sresp = mk_subresp(order_id, merchant, method, amount)
#                 stime = order_dt.strftime("%Y-%m-%d %H:%M:%S")

#                 if random.random() < 0.3:
#                     qr = None; qres = None; qtime = None
#                 else:
#                     qr = json.dumps({"query":"status","orderId":order_id}, ensure_ascii=False)
#                     qres = json.dumps({"status": random.choice(statuses)}, ensure_ascii=False)
#                     qtime = (order_dt + timedelta(minutes=random.randint(1,1440))).strftime("%Y-%m-%d %H:%M:%S")

#                 if random.random() < 0.05:
#                     cb = json.dumps({"callback":"ok","orderId":order_id}, ensure_ascii=False)
#                     cbtime = (order_dt + timedelta(minutes=random.randint(1,10080))).strftime("%Y-%m-%d %H:%M:%S")
#                 else:
#                     cb = None; cbtime = None

#                 vals = [
#                     esc(order_id),
#                     "0",
#                     str(acct),
#                     esc(sr),
#                     esc(sresp),
#                     esc(stime),
#                     (esc(qr) if qr is not None else "NULL"),
#                     (esc(qres) if qres is not None else "NULL"),
#                     (esc(qtime) if qtime is not None else "NULL"),
#                     (esc(cb) if cb is not None else "NULL"),
#                     (esc(cbtime) if cbtime is not None else "NULL")
#                 ]
#                 rows.append("(" + ",".join(vals) + ")")
#             stmt = header + ",\n".join(rows) + ";\n"
#             f.write(stmt)
#             written += take
#             if written % 100000 == 0:
#                 print(f"Written {written} rows...")
#     print("Done. file:", out_path)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--out", default="fake_t_order_http_log_1M.sql.gz")
#     parser.add_argument("--rows", type=int, default=1000000)
#     parser.add_argument("--batch", type=int, default=1000)
#     args = parser.parse_args()
#     make_generator(num_rows=args.rows, batch_size=args.batch, out_path=args.out)


#!/usr/bin/env python3
"""
Generate fake SQL INSERTs for g_paypay.t_order_http_log
Usage:
    python3 generate_fake_sql_1M.py \
        --out ./fake_t_order_http_log_10M_2025_08_11.sql.gz \
        --rows 10000000 \
        --batch 1000

Notes:
- Only generates data between 2025-08-01 ~ 2025-11-30
- Writes gzipped SQL file
"""

import argparse, gzip, json, random
from datetime import datetime, timedelta

def make_generator(num_rows=50000000, batch_size=10000, out_path="fake_t_order_http_log_10M_2025_08_11.sql.gz"):
    # ✅ 時間範圍限定在 2025-08 ~ 2025-11
    start_dt = datetime(2025, 10, 1, 0, 0, 0)
    end_dt = datetime(2025, 11, 30, 23, 59, 59)
    total_seconds = int((end_dt - start_dt).total_seconds())

    account_ids = [949, 1027, 1244, 1500, 2001, 3050, 4123, 587, 678, 1111]
    merchant_codes = ["587678", "24h497449", "15705852", "A1001", "B2002", "C3003"]
    emails = [f"user{i}@example.com" for i in range(1, 51)]
    names = [f"Name{i}" for i in range(1, 51)]
    payment_methods = ["QRIS", "bank_qr", "momo_bank", "QUICK.BANKVA", "ALIPAY", "GCASH"]
    statuses = ["PROCESSING", "SUCCESS", "FAILED", "PENDING"]

    def rand_dt_iso():
        dt = start_dt + timedelta(seconds=random.randint(0, total_seconds))
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def esc(s):
        if s is None:
            return "NULL"
        return "'" + s.replace("'", "''") + "'"

    def mk_subreq(order_id, merchant, method, amount):
        if method == "QRIS":
            obj = {
                "amount": str(amount),
                "customer": {
                    "email": random.choice(emails),
                    "name": random.choice(names),
                    "phone": str(random.randint(8000000000, 8999999999))
                },
                "merchantCode": merchant,
                "merchantNotifyUrl": f"https://gpay.dfgame.club/notify/{merchant}",
                "merchantOrderId": order_id,
                "paymentMethodCode": method
            }
        elif method in ("bank_qr", "momo_bank"):
            obj = {
                "merchantNo": f"{random.randint(100000,999999)}",
                "outTradeNo": order_id,
                "type": method,
                "code": method,
                "amount": str(amount),
                "timestamp": random.randint(1500000000, 1762227644),
                "notifyUrl": "https://gpay.dfgame.club/notify/24hpay",
                "sign": "%032x" % random.getrandbits(128)
            }
        else:
            obj = {
                "out_trade_no": order_id,
                "total_fee": str(amount),
                "trade_type": method,
                "notify_url": "https://gpay.dfgame.club/notify/xnetpay",
                "mch_id": str(random.randint(15000000,15999999))
            }
        return json.dumps(obj, ensure_ascii=False)

    def mk_subresp(order_id, merchant, method, amount):
        if method == "QRIS":
            resp = {
                "code": 200,
                "msg": "success",
                "data": {
                    "merchantCode": merchant,
                    "merchantOrderId": order_id,
                    "amount": f"{amount}.00",
                    "status": random.choice(statuses),
                    "paymentMethodCode": method
                }
            }
        elif method in ("bank_qr", "momo_bank"):
            resp = {
                "code": "200",
                "data": f"https://pay.example.com/{method}.html?{random.getrandbits(160):x}",
                "success": True,
                "message": "success"
            }
        else:
            resp = {
                "order_no": f"S{random.randint(1000000000,9999999999)}",
                "out_trade_no": order_id,
                "total_fee": str(amount),
                "return_msg": "SUCCESS",
                "return_code": "SUCCESS"
            }
        return json.dumps(resp, ensure_ascii=False)

    header = (
        "INSERT INTO g_paypay.t_order_http_log "
        "(OrderId,Type,AccountId,SubmitRequest,SubmitResponse,SubmitTime,"
        "QueryRequest,QueryResponse,QueryTime,CallbackRequest,CallbackTime) VALUES\n"
    )

    written = 0
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        while written < num_rows:
            rows = []
            take = min(batch_size, num_rows - written)
            for _ in range(take):
                order_dt = start_dt + timedelta(seconds=random.randint(0, total_seconds))
                order_id = "PAY" + order_dt.strftime("%Y%m%d%H%M%S") + f"{random.randint(100000,999999)}"
                acct = random.choice(account_ids)
                merchant = random.choice(merchant_codes)
                method = random.choice(payment_methods)
                amount = random.choice([10000, 50000, 70000, 500000, 700000, 1000000])

                sr = mk_subreq(order_id, merchant, method, amount)
                sresp = mk_subresp(order_id, merchant, method, amount)
                stime = order_dt.strftime("%Y-%m-%d %H:%M:%S")

                if random.random() < 0.3:
                    qr = qres = qtime = None
                else:
                    qr = json.dumps({"query": "status", "orderId": order_id}, ensure_ascii=False)
                    qres = json.dumps({"status": random.choice(statuses)}, ensure_ascii=False)
                    qtime = (order_dt + timedelta(minutes=random.randint(1, 1440))).strftime("%Y-%m-%d %H:%M:%S")

                if random.random() < 0.05:
                    cb = json.dumps({"callback": "ok", "orderId": order_id}, ensure_ascii=False)
                    cbtime = (order_dt + timedelta(minutes=random.randint(1, 10080))).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    cb = cbtime = None

                vals = [
                    esc(order_id), "0", str(acct),
                    esc(sr), esc(sresp), esc(stime),
                    esc(qr) if qr else "NULL",
                    esc(qres) if qres else "NULL",
                    esc(qtime) if qtime else "NULL",
                    esc(cb) if cb else "NULL",
                    esc(cbtime) if cbtime else "NULL"
                ]
                rows.append("(" + ",".join(vals) + ")")

            stmt = header + ",\n".join(rows) + ";\n"
            f.write(stmt)
            written += take
            if written % 100000 == 0:
                print(f"Written {written} rows...")
    print("✅ Done. file:", out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="fake_t_order_http_log_10M_2025_08_11.sql.gz")
    parser.add_argument("--rows", type=int, default=10000000)
    parser.add_argument("--batch", type=int, default=1000)
    args = parser.parse_args()
    make_generator(num_rows=args.rows, batch_size=args.batch, out_path=args.out)
