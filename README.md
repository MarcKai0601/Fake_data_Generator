
# 📘 MySQL 大量假資料產生與匯入工具

## 📌 專案簡介
本專案提供：

- **假資料 SQL 產生器 (`generate_fake_sql_1M.py`)**
- **MySQL 分批匯入工具 (`sql_stream_loader.py`)**

用途包含：

- 壓力測試（Stress Test）
- 大量資料灌入（100 萬筆以上）
- ETL / Data Migration 測試
- 效能驗證、Demo

---

## 🧱 專案結構

```
python_workspace/
│
├── generate_fake_sql_1_000_000.py     # 假資料產生器
├── sql_stream_loader.py               # MySQL 批次匯入工具
├── fake_t_order_http_log_1M.sql.gz    # 假資料 (壓縮)
├── fake_t_order_http_log_1M.sql       # 假資料 (解壓)
└── loader.progress                    # 匯入續傳檔
```

---

# 🔧 安裝與環境準備

## 1️⃣ 建立 Python 虛擬環境（建議）
```bash
mkdir -p ~/python_workspace && cd ~/python_workspace
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mysql-connector-python
```

> **啟用確認方式：**  
> 命令列前面有 `(.venv)` 或：
> ```bash
> echo $VIRTUAL_ENV
> ```

---

# 🛠 產生假資料

## 2️⃣ 生成 100 萬筆假資料（壓縮檔）
```bash
python generate_fake_sql_1M.py \
  --out /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql.gz \
  --rows 1000000 \
  --batch 1000
```

---

# 🗜 解壓 SQL（loader 必須使用 .sql）
```bash
gunzip -c \
  /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql.gz \
  > /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql
```

確認：

```bash
ls -lh fake_t_order_http_log_1M.sql
head -n 3 fake_t_order_http_log_1M.sql
```

---

# 📥 匯入假資料到 MySQL

## 方法 A（最快速）— MySQL CLI

```bash
mysql -h HOST -P 3306 -u root -p'PASSWORD' DATABASE \
  < /path/to/fake_t_order_http_log_1M.sql
```

---

## 方法 B（可續傳）— Python Loader

```bash
python sql_stream_loader.py \
  --input /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql \
  --host 192.168.1.171 --port 3306 \
  --user root --password 'PASSWORD' \
  --database g_paypay \
  --batch-statements 50 \
  --progress /Users/kai/Desktop/python_workspace/loader.progress \
  --print-progress-every 500
```

### 參數說明
| 參數 | 說明 |
|------|------|
| `--input` | `.sql` 或 `.gz` 檔案 |
| `--batch-statements` | 每次提交多少 SQL（建議 50–200） |
| `--progress` | 續傳 offset |
| `--print-progress-every` | 進度輸出頻率 |

---

# ⚠ 注意事項

### 1️⃣ `.sql.gz` 必須解壓後 loader 才能正確解析  
### 2️⃣ SQL 必須每條以 `;` 結尾  
### 3️⃣ loader 卡住 → 多半是**第一條 SQL 太大**  
### 4️⃣ 重跑前務必清除 progress
```bash
rm -f loader.progress
```
### 5️⃣ 匯入大量資料建議關閉外鍵 & 唯一檢查

匯入前：
```sql
SET autocommit=0;
SET unique_checks=0;
SET foreign_key_checks=0;
```

匯入後：
```sql
SET foreign_key_checks=1;
SET unique_checks=1;
COMMIT;
```

---

# ⚡ 效能比較

| 匯入方式 | 效能 | 適用 |
|----------|---------|----------|
| MySQL CLI | ⭐⭐⭐⭐⭐ | 最快、一次性匯入 |
| Loader batch=50 | ⭐⭐⭐⭐ | 可續傳、可控 |
| Loader batch=1 | ⭐ | 僅用於測試 |

---

# 🧪 匯入後驗證

```sql
SELECT COUNT(*) FROM t_order_http_log;
SELECT MIN(SubmitTime), MAX(SubmitTime) FROM t_order_http_log;
```

---

# 🧹 清除產生的檔案

```bash
rm fake_t_order_http_log_1M.sql
rm fake_t_order_http_log_1M.sql.gz
rm loader.progress
```

---
