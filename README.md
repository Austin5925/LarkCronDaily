# LarkCronDaily

每个美国银行工作日自动将飞书多维表格（Lark Bitable）中上一个有效交易日的所有行复制到今天。

## 功能

- 自动计算"上一个有效交易日"（排除周末 + 美国联邦银行假期）
- 在多维表格中筛选该日期的所有行
- 将这些行复制到今天的日期（仅修改日期字段，其余字段原样保留）
- 非交易日自动跳过

## 前置条件

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app) → 创建企业自建应用
2. 在「权限管理」中添加以下权限：
   - `bitable:app` — 多维表格读写权限
3. 在「版本管理与发布」中发布应用
4. 记录 **App ID** 和 **App Secret**

### 2. 获取多维表格标识

- 打开你的多维表格，URL 格式为：
  ```
  https://xxx.feishu.cn/base/{app_token}?table={table_id}&view=...
  ```
- `app_token`：`/base/` 后面的字符串
- `table_id`：`?table=` 后面的字符串

### 3. 授权应用访问多维表格

在多维表格右上角「...」→「更多」→「添加文档应用」，搜索并添加你创建的应用。

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd LarkCronDaily

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的实际值
```

## 手动运行

```bash
source venv/bin/activate
python main.py
```

## Cron 部署（Ubuntu VPS）

建议美东时间早上 7:00 执行（UTC 12:00）：

```bash
crontab -e
```

添加以下行：

```cron
0 12 * * 1-5 cd /path/to/LarkCronDaily && /path/to/LarkCronDaily/venv/bin/python main.py >> /var/log/lark_daily_copy_cron.log 2>&1
```

说明：
- `0 12 * * 1-5` — UTC 12:00，周一到周五执行
- 脚本内部会检查是否为有效交易日，假期会自动跳过
- cron 日志输出到 `/var/log/lark_daily_copy_cron.log`
- 脚本自身的详细日志写入 `lark_daily_copy.log`（由 `LOG_FILE` 环境变量控制）

## 项目结构

```
LarkCronDaily/
├── main.py              # 主脚本入口
├── config.py            # 配置（从 .env 加载）
├── lark_api.py          # 飞书 API 封装（认证、搜索、批量创建）
├── business_days.py     # 美国银行假期 & 有效交易日计算
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
└── README.md            # 本文件
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `LARK_APP_ID` | 是 | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | 飞书应用 App Secret |
| `BITABLE_APP_TOKEN` | 是 | 多维表格 app_token |
| `BITABLE_TABLE_ID` | 是 | 数据表 table_id |
| `DATE_FIELD_NAME` | 否 | 日期字段名（默认：`日期`） |
| `LARK_API_BASE` | 否 | API 基础 URL（默认：`https://open.feishu.cn`） |
| `LOG_FILE` | 否 | 日志文件路径（默认：`lark_daily_copy.log`） |

## 美国银行假期

脚本排除以下 Federal Reserve 官方假期：

- New Year's Day (1月1日)
- Martin Luther King Jr. Day (1月第3个周一)
- Presidents' Day (2月第3个周一)
- Memorial Day (5月最后一个周一)
- Juneteenth (6月19日)
- Independence Day (7月4日)
- Labor Day (9月第1个周一)
- Columbus Day (10月第2个周一)
- Veterans Day (11月11日)
- Thanksgiving Day (11月第4个周四)
- Christmas Day (12月25日)

假期落在周六时顺延到周五，落在周日时顺延到周一。

## 日志示例

```
2026-03-05 12:00:01 [INFO] Script started. Today is 2026-03-05 (Thursday).
2026-03-05 12:00:01 [INFO] Previous valid business day: 2026-03-04
2026-03-05 12:00:01 [INFO] Obtained tenant_access_token successfully.
2026-03-05 12:00:02 [INFO] Found 15 records for date 2026-03-04 (ts=1741046400000).
2026-03-05 12:00:02 [INFO] Prepared 15 new records (date: 2026-03-04 → 2026-03-05).
2026-03-05 12:00:03 [INFO] Batch 1: created 15 records.
2026-03-05 12:00:03 [INFO] Done. Copied 15 rows from 2026-03-04 to 2026-03-05.
```
