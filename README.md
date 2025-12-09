📌 專案簡介

本專案提供：

假資料 SQL 產生器 (generate_fake_sql_1M.py)

MySQL 分批匯入工具 (sql_stream_loader.py)

用途包含：

壓力測試（Stress Test）

大量資料灌入（100 萬筆以上）

ETL / Data Migration 測試

效能驗證、Demo

🧱 專案結構
python_workspace/
│
├── generate_fake_sql_1M.py          # 假資料產生器
├── sql_stream_loader.py             # MySQL 批次匯入工具
├── fake_t_order_http_log_1M.sql.gz  # 假資料 (壓縮)
├── fake_t_order_http_log_1M.sql     # 假資料 (解壓)
└── loader.progress                  # 匯入續傳檔

🔧 安裝與環境準備
1️⃣ 建立 Python 虛擬環境（建議）
mkdir -p ~/python_workspace && cd ~/python_workspace
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mysql-connector-python


⚠ 虛擬環境確認方式：
若你的命令列前面有 (.venv) → 就是啟用中。
或可用：

echo $VIRTUAL_ENV

🛠 產生假資料
2️⃣ 生成 100 萬筆假資料（壓縮檔）
python generate_fake_sql_1M.py \
  --out /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql.gz \
  --rows 1000000 \
  --batch 1000


完成後會看到：

Written 1000000 rows...
Done.

🗜 解壓 SQL（loader 必須使用 .sql）
gunzip -c \
  /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql.gz \
  > /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1M.sql


確認檔案：

ls -lh fake_t_order_http_log_1M.sql
head -n 3 fake_t_order_http_log_1M.sql

📥 匯入假資料到 MySQL
方法 A（最快速）💨 — MySQL CLI 直接匯入
mysql -h 192.168.1.171 -P 3306 -u root -p'YOUR_PASSWORD' g_paypay \
  < /Users/kai/Desktop/python_workspace/fake_t_order_http_log_1_000_000.sql


✔ 適合大量灌資料，速度最快
✘ 不支援續傳

方法 B（可中斷續傳）🐍 — Python Loader 匯入
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
--input	.sql 檔案路徑
--batch-statements	每次提交多少條 SQL（建議 50～200）
--progress	儲存 offset，可中斷續傳
--print-progress-every	印出進度的頻率
中斷後續傳
python sql_stream_loader.py --input ... --same-options...

⚠ 注意事項（重要）
1️⃣ .sql.gz 不可直接匯入 loader（需先解壓）

loader 只能讀可解析的 SQL。

2️⃣ .sql 必須以分號 ; 結尾

否則 loader 會判定無法執行 SQL
症狀：

All done. statements: 0

3️⃣ 若 loader 看起來卡住 → 其實是在讀第一條巨大 SQL

可切換測試模式：

--batch-statements 1
--print-progress-every 1


確認正常後再改回 50。

4️⃣ 若重跑記得刪掉 progress 檔案

避免 offset 錯置：

rm -f loader.progress

5️⃣ 匯入期間建議關閉外鍵/唯一檢查（大幅加速）

匯入前：

SET autocommit=0;
SET unique_checks=0;
SET foreign_key_checks=0;


匯入後：

SET foreign_key_checks=1;
SET unique_checks=1;
COMMIT;

⚡ 效能比較
匯入方式	效能	適用
MySQL CLI < file.sql	⭐⭐⭐⭐⭐ 最快	單純灌資料
Python Loader（batch=50）	⭐⭐⭐⭐	可續傳、可控
Loader（batch=1）	⭐	測試用
🧪 匯入後驗證資料
SELECT COUNT(*) FROM t_order_http_log;
SELECT MIN(SubmitTime), MAX(SubmitTime) FROM t_order_http_log;

🧹 清除產生的檔案（可選）
rm fake_t_order_http_log_1M.sql
rm fake_t_order_http_log_1M.sql.gz
rm loader.progress

🧩 Troubleshooting（FAQ）
❓ 匯入顯示 statements: 0

→ .sql 沒分號 / .sql 是空的 / loader 讀不到檔案

❓ 匯入卡住

→ 第一條 SQL 太長 → 不是卡住，只是在讀取
→ 使用：

--batch-statements 1 --print-progress-every 1

❓ Python 版本衝突

→ 啟用虛擬環境：

source .venv/bin/activate
