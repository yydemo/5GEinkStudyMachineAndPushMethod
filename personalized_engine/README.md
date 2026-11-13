# 个性化试卷与资料引擎，以及 AI 自习室工具

依据考试试卷、逐题作答和选科组合，为每名学生生成一份可下发到墨水屏（或打印）的个性化练习与分层资料，并附带教师审核摘要。在此之上，增加 AI 自习室运营能力：按薄弱科目安排座位与场次、读取签到记录、生成学情周报，以及按假设参数测算单店财务。

本版本是**可运行的规则引擎框架**。后续可用大模型替换生成模块，但当前**不调用任何外部 API**。请先用 `data/sample/` 中的示例数据跑通流程，再替换为真实数据。

调研说明见仓库文档 [`docs/ai_study_room_report.md`](../docs/ai_study_room_report.md)。

## 安装

在本目录下执行：

```bash
python -m venv .venv
source .venv/bin/activate   # Windows 使用 .venv\Scripts\activate
pip install -e ".[dev]"
```

安装后可使用命令 `eink-studyroom`。若不做安装，仍可像第一版一样：

```bash
pip install -r requirements.txt
python -m src.main --data data/sample --out output
pytest -q
```

## 命令

```bash
# 生成每生个性化材料与教师审核摘要（与 python -m src.main 相同）
eink-studyroom generate --data data/sample --out output

# 按薄弱科目排座位场次，并生成学情周报
eink-studyroom report --data data/sample --out output --week-start 2026-11-02

# 按 config.yaml 中的假设参数输出单店测算
eink-studyroom finance --out output

# 依次执行以上三步
eink-studyroom all --data data/sample --out output
```

成功后会得到：

- `output/students/S001.md` … 每名学生一份 Markdown 学习材料
- `output/教师审核摘要.md` 供教师快速审核
- `output/studyroom/座位与场次安排.md`（及 CSV）
- `output/studyroom/weekly/S001_学情周报.md` … 每生一份周报
- `output/studyroom/学情周报汇总.md`
- `output/studyroom/单店测算.md`

可选参数：`--config config.yaml`、`--save-processed`（将清洗后的数据快照写入 `output/_processed/`）。

将 CLI 打包为单文件可执行程序（可选，不提交二进制）：

```bash
bash scripts/build_exe.sh
```

## 流水线

```
学生信息（仅学习字段） + 考试成绩 + 逐题作答 + 题库
        ↓  data_loader / cleaner
学情画像（profiler）
        ↓
知识点掌握度 + 薄弱点排序（analyzer）
        ↓
错题重练 + 分层资料（generator，规则引擎；预留大模型接口）
        ↓
每生 Markdown + 教师审核摘要（exporter）

同时（AI 自习室）：

薄弱科目 + 场次座位规则 → 座位与场次安排
签到记录 + 学情 → 学情周报（无私人信息）
config.yaml 情景参数 → 单店测算.md
```

掌握度计算规则：

- 只分析该生**选科组合内**的科目；
- 取该知识点**最近 3 次**相关考试，按配置加权（默认 0.5 / 0.3 / 0.2）；
- **错题权重更高**（默认 1.8），会更明显地拉低掌握度；
- 薄弱点排序综合考虑：掌握度低、出现频次高、近期呈下降趋势。

生成策略：

- **错题重练**：优先收录原错题，再用题库中同一知识点的新题补足；
- **分层资料**：按掌握度分为基础 / 中等 / 拓展，并附简短概念提示；
- **容量限制**：题量与预估页数可在 `config.yaml` 中配置，以适配墨水屏。

大模型接口：`src/generator.py` 中的 `MaterialGenerator` / `LLMGenerator`。把 `config.yaml` 的 `generator.backend` 改为 `llm` 会走到该预留类；本版本其中的 `generate()` 会明确报错，不会发起网络请求。实现校内部署模型后，只需改这一处。

自习室规则：

- 座位安排优先按薄弱科目把学生分到理科或文科辅导区，同一场次座位不重复；
- 周报只使用学号、年级班级、选科、出勤和知识点等学习字段；
- 单店测算的全部数字都是假设参数下的计算结果，不是经营事实。

## 输入文件格式

把真实数据放到一个目录（例如 `data/raw/`）中，文件名如下。CSV 与 JSON 均可，同名时优先读 CSV。编码使用 UTF-8。

所有表示列表示例数据见 `data/sample/`（**SYNTHETIC / 示例数据**，仅用于演示，不是真实学生）。

### students.csv（必填）

只保留学习相关字段。若文件中还有姓名、手机、身份证等列，加载器会**自动丢弃**。

| 字段 | 说明 |
|------|------|
| student_id | 内部学号，不要使用真实姓名 |
| grade | 年级，如 `高二` |
| class_name | 班级，如 `3班` |
| subject_track | 选科组合，如 `物化生`、`史地生` |
| subjects | 科目列表，逗号分隔，如 `物理,化学,生物`。若为空，将按选科组合推断 |

JSON 等价形式为对象数组，字段名相同。

### exams.csv（可选，建议提供）

| 字段 | 说明 |
|------|------|
| exam_id | 考试编号 |
| exam_name | 考试名称 |
| subject | 科目 |
| exam_date | 日期，`YYYY-MM-DD` |
| full_score | 满分 |

若缺省，将从成绩或答题记录推断。

### scores.csv（可选，建议提供）

| 字段 | 说明 |
|------|------|
| exam_id | 考试编号 |
| student_id | 学号 |
| subject | 科目 |
| score | 得分 |
| full_score | 满分 |
| exam_date | 可省略，将用 exams 表补全 |

若缺省，将按答题得分汇总。

### answers.csv（必填）

逐题作答，是掌握度分析的核心输入。

| 字段 | 说明 |
|------|------|
| exam_id | 考试编号 |
| student_id | 学号 |
| question_id | 题目编号 |
| knowledge_points | 知识点，逗号或顿号分隔 |
| is_correct | 对错：`true/false`、`1/0`、`是/否`、`对/错` 均可 |
| score | 该题得分，支持部分分 |
| full_score | 该题满分 |
| error_type | 可选，如 `概念混淆` |
| subject | 可选，缺省时用考试科目补全 |

### question_bank.csv（建议提供）

题库与试卷原题可放在同一张表：来自某次考试的题目填写 `exam_id`，补充练习题将 `exam_id` 留空。

| 字段 | 说明 |
|------|------|
| question_id | 题目编号，需能与 answers 对应 |
| subject | 科目 |
| knowledge_points | 知识点 |
| difficulty | `基础` / `中等` / `拓展`（也接受 简单、困难 等别名） |
| stem | 题干 |
| exam_id | 若是试卷原题则填写考试编号，题库新题留空 |
| explanation | 可选解析或提示 |

### checkins.csv（学情周报需要）

自习室签到记录。示例见 `data/sample/checkins.csv`。

| 字段 | 说明 |
|------|------|
| checkin_id | 记录编号 |
| student_id | 内部学号 |
| date | 日期，`YYYY-MM-DD` |
| slot_id | 场次编号，如 `WD_EV`、`WE_PM` |
| seat_id | 座位编号 |
| subject_focus | 本场重点科目 |
| planned_minutes | 应到时长（分钟） |
| attended | 是否到馆：`true/false`、`1/0`、`是/否` 均可 |
| duration_minutes | 实到时长，缺勤应为 0 |

不要在此文件中写入姓名或联系方式。

## 目录说明

```
personalized_engine/
├── README.md
├── pyproject.toml          # pip install -e . 后提供 eink-studyroom 命令
├── requirements.txt
├── config.yaml
├── scripts/build_exe.sh    # 可选，PyInstaller 打包（不提交二进制）
├── data/
│   ├── raw/                # 放置后续真实数据（不要写入姓名等私人信息）
│   ├── processed/          # 预留清洗结果
│   └── sample/             # 示例数据（已标注，可直接跑通）
├── src/
│   ├── data_loader.py
│   ├── cleaner.py
│   ├── profiler.py
│   ├── analyzer.py
│   ├── generator.py        # 含大模型预留接口
│   ├── exporter.py
│   ├── main.py             # python -m src.main
│   ├── cli.py              # eink-studyroom 入口
│   └── studyroom/          # 排座、签到、周报、财务测算
├── tests/
└── output/                 # 运行产出，已加入 .gitignore
```

## 隐私约定

- 输入与输出都只使用内部学号和年级、班级、选科、答题、出勤等学习字段；
- 不要把真实姓名、联系方式、家庭信息或其他无关私人数据放入本目录或提交到仓库；
- 教师审核摘要和学情周报同样不含真实姓名；
- 真实数据放在 `data/raw/`，该目录已被忽略，不会进入公开仓库。
