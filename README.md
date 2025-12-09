📌 專案簡介

此專案包含：

假資料產生器：可生成大量 SQL INSERT 語句（含隨機時間、帳號、JSON payload 等）。

批次匯入工具（loader）：可將大型 SQL 檔（含 .gz 壓縮檔）分批匯入 MySQL。

適用於：

壓力測試

前後端 Demo 資料準備

ETL / 資料遷移演練

大量寫入效能測試

🧱 目錄結構
python_workspace/
│
├── generate_fake_sql_1M.py       # 假資料產生器
├── sql_stream_loader.py          # 分批匯入 MySQL 工具
├── fake_t_order_http_log_1M.sql.gz (產生後會出現)
├── fake_t_order_http_log_1M.sql   (解壓後)
└── loader.progress               # 匯入續傳檔 (自動生成)

🔧 安裝與環境準備
1️⃣ 建立 Python 虛擬環境（建議）
mkdir -p ~/python_workspace && cd ~/python_workspace
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mysql-connector-python


使用虛擬環境可避免 Homebrew/Python 版本衝突。

🛠 功能一：生成假資料 SQL
產生 100 萬筆（壓縮檔）
python generate_fake_sql_1M.py \
  --out /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql.gz \
  --rows 1000000 \
  --batch 1000


產生完成後會看到：

Written 1000000 rows...
Done.

🔧 功能二：解壓 SQL 檔案（如需 loader 匯入）
gunzip -c /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql.gz \
  > /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql


確認：

ls -lh fake_t_order_http_log_1M.sql
head -n 3 fake_t_order_http_log_1M.sql

📥 功能三：匯入資料到 MySQL
方法 A（最快）💨 — MySQL CLI 直接匯入

適用於乾淨灌資料、不需要 resume。

mysql -h 192.168.1.171 -P 3306 -u root -p'YOUR_PASSWORD' g_paypay \
  < /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql

方法 B（可中斷 & 可 resume）🐍 — Python Loader
基本匯入方式
python sql_stream_loader.py \
  --input /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql \
  --host 192.168.1.171 --port 3306 \
  --user root --password 'YOUR_PASSWORD' \
  --database g_paypay \
  --batch-statements 50 \
  --progress /Users/kai/Desktop/python_workspace/loader.progress \
  --print-progress-every 500

參數說明
參數	說明
--input	.sql 或 .sql.gz 檔案
--batch-statements	每次提交多少 SQL（建議 50–200）
--progress	儲存續傳 offset（中斷可接續）
--print-progress-every	每 N 條印一次進度
中斷後續傳
python sql_stream_loader.py --input ... --same-options...


只要 loader.progress 還在，就會從上一個 offset 繼續。

⚠ 注意事項（必看）
1️⃣ .sql.gz 不能直接給 loader（需要解壓）

若用 .gz 請務必：

gunzip -c xxx.sql.gz > xxx.sql

2️⃣ 確保每條 SQL 都用「;」結尾

loader 用分號分句，沒分號會導致：

statements: 0

3️⃣ loader 若顯示卡住 → 很可能是在讀第一條超長 SQL

解法：

--batch-statements 1 --print-progress-every 1

4️⃣ MySQL 若速度太慢

可在匯入前加入：

SET autocommit=0;
SET unique_checks=0;
SET foreign_key_checks=0;


匯入後：

SET foreign_key_checks=1;
SET unique_checks=1;
COMMIT;

5️⃣ 若主鍵重複（OrderId），匯入會被 rollback

建議假資料 OrderId 使用：

時間戳 + 隨機數

或 UUID

6️⃣ loader.progress 建議在重新跑前刪除

避免 offset 混亂：

rm -f loader.progress

⚡ 效能建議
方法	性能	適用情境
MySQL CLI < file.sql	⭐⭐⭐⭐⭐ 最快	大量一次性匯入
Loader batch = 200	⭐⭐⭐⭐	可控、可續傳
Loader batch = 1	⭐	測試用，不適合大量匯入
🧪 匯入後驗證
SELECT COUNT(*) FROM t_order_http_log;
SELECT MIN(SubmitTime), MAX(SubmitTime) FROM t_order_http_log;

🧹 清除匯入檔案
rm fake_t_order_http_log_1M.sql
rm fake_t_order_http_log_1M.sql.gz
rm loader.progress
