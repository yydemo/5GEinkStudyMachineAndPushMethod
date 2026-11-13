# 个性化试卷与资料引擎，以及 AI 自习室工具 / Personalized Exam & Materials Engine, plus AI Study-Room Tools

> 语言说明 / Language note：本文、代码注释、命令行提示与生成的材料均为中英双语，先中文后英文。 / This document, code comments, CLI messages and generated materials are all bilingual: Chinese first, then English.

依据考试试卷、逐题作答和选科组合，为每名学生生成一份可下发到墨水屏（或打印）的个性化练习与分层资料，并附带教师审核摘要。在此之上，增加 AI 自习室运营能力：按薄弱科目安排座位与场次、读取签到记录、生成学情周报，以及按假设参数测算单店财务。

Based on exam papers, per-question answers and subject combinations, it generates for each student one pack of personalized practice and tiered materials that can be pushed to an E-Ink device (or printed), together with a teacher review summary. On top of that it adds AI study-room operations: seat and session assignment by weak subject, reading check-in records, generating weekly learning reports, and estimating single-store finances from assumed parameters.

本版本是**可运行的规则引擎框架**。后续可用大模型替换生成模块，但当前**不调用任何外部 API**。请先用 `data/sample/` 中的示例数据跑通流程，再替换为真实数据。

This version is a **runnable rule-engine framework**. The generation module can later be replaced by a large model, but it currently **calls no external APIs**. Run the pipeline with the sample data in `data/sample/` first, then switch to real data.

调研说明见仓库文档 [`docs/ai_study_room_report.md`](../docs/ai_study_room_report.md)。

For the research write-up, see [`docs/ai_study_room_report.md`](../docs/ai_study_room_report.md).

## 安装 / Installation

在本目录下执行：

Run in this directory:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows 使用 / on Windows use: .venv\Scripts\activate
pip install -e ".[dev]"
```

安装后可使用命令 `eink-studyroom`。若不做安装，仍可像第一版一样：

After installation the `eink-studyroom` command is available. Without installing, you can still run it as in the first version:

```bash
pip install -r requirements.txt
python -m src.main --data data/sample --out output
pytest -q
```

## 命令 / Commands

```bash
# 生成每生个性化材料与教师审核摘要（与 python -m src.main 相同）
# Generate per-student personalized materials and the teacher review summary (same as python -m src.main)
eink-studyroom generate --data data/sample --out output

# 按薄弱科目排座位场次，并生成学情周报
# Assign seats/sessions by weak subject and generate weekly learning reports
eink-studyroom report --data data/sample --out output --week-start 2026-11-02

# 按 config.yaml 中的假设参数输出单店测算
# Output the single-store estimate from the assumed parameters in config.yaml
eink-studyroom finance --out output

# 依次执行以上三步
# Run all three steps above in order
eink-studyroom all --data data/sample --out output
```

成功后会得到：

On success you get:

- `output/students/S001.md` … 每名学生一份 Markdown 学习材料 / one Markdown learning pack per student
- `output/教师审核摘要.md` 供教师快速审核 / teacher review summary for quick review
- `output/studyroom/座位与场次安排.md`（及 CSV） / seat and session plan (plus CSV)
- `output/studyroom/weekly/S001_学情周报.md` … 每生一份周报 / one weekly report per student
- `output/studyroom/学情周报汇总.md` / weekly report overview
- `output/studyroom/单店测算.md` / single-store estimate

（输出文件名保持中文，以兼容已有脚本；文件内容为中英双语。 / Output file names stay in Chinese for compatibility with existing scripts; file contents are bilingual.）

可选参数：`--config config.yaml`、`--save-processed`（将清洗后的数据快照写入 `output/_processed/`）。

Optional arguments: `--config config.yaml`, `--save-processed` (writes a snapshot of the cleaned data to `output/_processed/`).

将 CLI 打包为单文件可执行程序（可选，不提交二进制）：

Package the CLI as a single-file executable (optional; never commit the binary):

```bash
bash scripts/build_exe.sh
```

## 流水线 / Pipeline

```
学生信息（仅学习字段） + 考试成绩 + 逐题作答 + 题库
Student info (learning fields only) + exam scores + per-question answers + question bank
        ↓  data_loader / cleaner
学情画像（profiler） / Learning profile (profiler)
        ↓
知识点掌握度 + 薄弱点排序（analyzer） / Knowledge-point mastery + weak-point ranking (analyzer)
        ↓
错题重练 + 分层资料（generator，规则引擎；预留大模型接口）
Mistake re-practice + tiered materials (generator, rule engine; LLM interface reserved)
        ↓
每生 Markdown + 教师审核摘要（exporter） / Per-student Markdown + teacher review summary (exporter)

同时（AI 自习室） / In parallel (AI study room):

薄弱科目 + 场次座位规则 → 座位与场次安排 / Weak subjects + session/seat rules → seat and session plan
签到记录 + 学情 → 学情周报（无私人信息） / Check-ins + learning data → weekly reports (no private info)
config.yaml 情景参数 → 单店测算.md / config.yaml scenario parameters → single-store estimate
```

掌握度计算规则 / Mastery calculation rules:

- 只分析该生**选科组合内**的科目； / Only subjects **within the student's subject combination** are analysed;
- 取该知识点**最近 3 次**相关考试，按配置加权（默认 0.5 / 0.3 / 0.2）； / The **3 most recent** exams covering the knowledge point are used, weighted per config (default 0.5 / 0.3 / 0.2);
- **错题权重更高**（默认 1.8），会更明显地拉低掌握度； / **Wrong answers weigh more** (default 1.8), pulling mastery down more visibly;
- 薄弱点排序综合考虑：掌握度低、出现频次高、近期呈下降趋势。 / Weak-point ranking combines low mastery, high frequency and a recent declining trend.

生成策略 / Generation strategy:

- **错题重练**：优先收录原错题，再用题库中同一知识点的新题补足； / **Mistake re-practice**: original wrong questions first, topped up with new questions on the same knowledge point from the bank;
- **分层资料**：按掌握度分为基础 / 中等 / 拓展，并附简短概念提示； / **Tiered materials**: split by mastery into basic / intermediate / advanced, with short concept hints;
- **容量限制**：题量与预估页数可在 `config.yaml` 中配置，以适配墨水屏。 / **Capacity limits**: question count and estimated pages are configurable in `config.yaml` to fit E-Ink screens.

大模型接口：`src/generator.py` 中的 `MaterialGenerator` / `LLMGenerator`。把 `config.yaml` 的 `generator.backend` 改为 `llm` 会走到该预留类；本版本其中的 `generate()` 会明确报错，不会发起网络请求。实现校内部署模型后，只需改这一处。

LLM interface: `MaterialGenerator` / `LLMGenerator` in `src/generator.py`. Setting `generator.backend` in `config.yaml` to `llm` routes to that reserved class; in this version its `generate()` raises an explicit error and makes no network request. Once a campus-hosted model is implemented, only this one place needs to change.

自习室规则 / Study-room rules:

- 座位安排优先按薄弱科目把学生分到理科或文科辅导区，同一场次座位不重复； / Seat assignment puts students into the science or humanities tutoring zone by weak subject first; no seat is reused within a session;
- 周报只使用学号、年级班级、选科、出勤和知识点等学习字段； / Weekly reports use only learning fields such as student ID, grade/class, subject combination, attendance and knowledge points;
- 单店测算的全部数字都是假设参数下的计算结果，不是经营事实。 / All single-store estimate figures are computed from assumed parameters, not operating facts.

## 输入文件格式 / Input file formats

把真实数据放到一个目录（例如 `data/raw/`）中，文件名如下。CSV 与 JSON 均可，同名时优先读 CSV。编码使用 UTF-8。

Put real data in one directory (e.g. `data/raw/`) with the file names below. CSV and JSON are both accepted; CSV wins when both exist. Use UTF-8 encoding.

所有表示列表示例数据见 `data/sample/`（**SYNTHETIC / 示例数据**，仅用于演示，不是真实学生）。

Example data for every table is in `data/sample/` (**SYNTHETIC / 示例数据**, for demonstration only, not real students).

（列名保持原样，不要翻译。 / Column names stay as-is; do not translate them.）

### students.csv（必填 / required）

只保留学习相关字段。若文件中还有姓名、手机、身份证等列，加载器会**自动丢弃**。

Only learning-related fields are kept. If the file also has name, phone, ID-card or similar columns, the loader **drops them automatically**.

| 字段 / Field | 说明 / Description |
|------|------|
| student_id | 内部学号，不要使用真实姓名 / Internal student ID; never use real names |
| grade | 年级，如 `高二` / Grade, e.g. `高二` (Senior 2) |
| class_name | 班级，如 `3班` / Class, e.g. `3班` (Class 3) |
| subject_track | 选科组合，如 `物化生`、`史地生` / Subject combination, e.g. `物化生` (physics-chemistry-biology), `史地生` (history-geography-biology) |
| subjects | 科目列表，逗号分隔，如 `物理,化学,生物`。若为空，将按选科组合推断 / Comma-separated subject list, e.g. `物理,化学,生物`; inferred from the combination if empty |

JSON 等价形式为对象数组，字段名相同。

The JSON equivalent is an array of objects with the same field names.

### exams.csv（可选，建议提供 / optional, recommended）

| 字段 / Field | 说明 / Description |
|------|------|
| exam_id | 考试编号 / Exam ID |
| exam_name | 考试名称 / Exam name |
| subject | 科目 / Subject |
| exam_date | 日期，`YYYY-MM-DD` / Date, `YYYY-MM-DD` |
| full_score | 满分 / Full score |

若缺省，将从成绩或答题记录推断。

If omitted, it is inferred from scores or answer records.

### scores.csv（可选，建议提供 / optional, recommended）

| 字段 / Field | 说明 / Description |
|------|------|
| exam_id | 考试编号 / Exam ID |
| student_id | 学号 / Student ID |
| subject | 科目 / Subject |
| score | 得分 / Score |
| full_score | 满分 / Full score |
| exam_date | 可省略，将用 exams 表补全 / Optional; filled from the exams table |

若缺省，将按答题得分汇总。

If omitted, it is aggregated from per-question scores.

### answers.csv（必填 / required）

逐题作答，是掌握度分析的核心输入。

Per-question answers — the core input for mastery analysis.

| 字段 / Field | 说明 / Description |
|------|------|
| exam_id | 考试编号 / Exam ID |
| student_id | 学号 / Student ID |
| question_id | 题目编号 / Question ID |
| knowledge_points | 知识点，逗号或顿号分隔 / Knowledge points, separated by commas or 、 |
| is_correct | 对错：`true/false`、`1/0`、`是/否`、`对/错` 均可 / Correctness: `true/false`, `1/0`, `是/否`, `对/错` all accepted |
| score | 该题得分，支持部分分 / Score for the question; partial credit supported |
| full_score | 该题满分 / Full score for the question |
| error_type | 可选，如 `概念混淆` / Optional, e.g. `概念混淆` (concept confusion) |
| subject | 可选，缺省时用考试科目补全 / Optional; filled from the exam subject if missing |

### question_bank.csv（建议提供 / recommended）

题库与试卷原题可放在同一张表：来自某次考试的题目填写 `exam_id`，补充练习题将 `exam_id` 留空。

The question bank and original exam questions can share one table: questions from an exam fill in `exam_id`; supplementary practice questions leave `exam_id` empty.

| 字段 / Field | 说明 / Description |
|------|------|
| question_id | 题目编号，需能与 answers 对应 / Question ID; must match answers |
| subject | 科目 / Subject |
| knowledge_points | 知识点 / Knowledge points |
| difficulty | `基础` / `中等` / `拓展`（也接受 简单、困难 等别名） / `基础` (basic) / `中等` (intermediate) / `拓展` (advanced); aliases such as 简单 (easy) and 困难 (hard) are accepted |
| stem | 题干 / Question stem |
| exam_id | 若是试卷原题则填写考试编号，题库新题留空 / Exam ID for original exam questions; empty for new bank questions |
| explanation | 可选解析或提示 / Optional explanation or hint |

### checkins.csv（学情周报需要 / needed for weekly reports）

自习室签到记录。示例见 `data/sample/checkins.csv`。

Study-room check-in records. See `data/sample/checkins.csv` for an example.

| 字段 / Field | 说明 / Description |
|------|------|
| checkin_id | 记录编号 / Record ID |
| student_id | 内部学号 / Internal student ID |
| date | 日期，`YYYY-MM-DD` / Date, `YYYY-MM-DD` |
| slot_id | 场次编号，如 `WD_EV`、`WE_PM` / Session ID, e.g. `WD_EV`, `WE_PM` |
| seat_id | 座位编号 / Seat ID |
| subject_focus | 本场重点科目 / Focus subject for the session |
| planned_minutes | 应到时长（分钟） / Planned duration (minutes) |
| attended | 是否到馆：`true/false`、`1/0`、`是/否` 均可 / Attended: `true/false`, `1/0`, `是/否` all accepted |
| duration_minutes | 实到时长，缺勤应为 0 / Actual duration; 0 if absent |

不要在此文件中写入姓名或联系方式。

Never put names or contact details in this file.

## 目录说明 / Directory layout

```
personalized_engine/
├── README.md
├── pyproject.toml          # pip install -e . 后提供 eink-studyroom 命令 / provides the eink-studyroom command after pip install -e .
├── requirements.txt
├── config.yaml
├── scripts/build_exe.sh    # 可选，PyInstaller 打包（不提交二进制） / optional PyInstaller build (never commit binaries)
├── data/
│   ├── raw/                # 放置后续真实数据（不要写入姓名等私人信息） / real data later (no names or other private info)
│   ├── processed/          # 预留清洗结果 / reserved for cleaned results
│   └── sample/             # 示例数据（已标注，可直接跑通） / sample data (labelled, runs out of the box)
├── src/
│   ├── data_loader.py
│   ├── cleaner.py
│   ├── profiler.py
│   ├── analyzer.py
│   ├── generator.py        # 含大模型预留接口 / includes the reserved LLM interface
│   ├── exporter.py
│   ├── main.py             # python -m src.main
│   ├── cli.py              # eink-studyroom 入口 / eink-studyroom entry point
│   └── studyroom/          # 排座、签到、周报、财务测算 / seating, check-ins, weekly reports, finance estimate
├── tests/
└── output/                 # 运行产出，已加入 .gitignore / run output, in .gitignore
```

## 隐私约定 / Privacy rules

- 输入与输出都只使用内部学号和年级、班级、选科、答题、出勤等学习字段； / Inputs and outputs use only internal student IDs and learning fields such as grade, class, subject combination, answers and attendance;
- 不要把真实姓名、联系方式、家庭信息或其他无关私人数据放入本目录或提交到仓库； / Never put real names, contact details, family information or other unrelated private data in this directory or commit them;
- 教师审核摘要和学情周报同样不含真实姓名； / Teacher review summaries and weekly reports likewise contain no real names;
- 真实数据放在 `data/raw/`，该目录已被忽略，不会进入公开仓库。 / Real data goes in `data/raw/`, which is git-ignored and never enters the public repository.
