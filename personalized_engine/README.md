# 个性化试卷与资料引擎（第一版框架）

依据考试试卷、逐题作答和选科组合，为每名学生生成一份可下发到墨水屏（或打印）的个性化练习与分层资料，并附带教师审核摘要。

本版本是**可运行的规则引擎框架**。后续可用大模型替换生成模块，但当前**不调用任何外部 API**。请先用 `data/sample/` 中的示例数据跑通流程，再替换为真实数据。

## 快速开始

在本目录下执行：

```bash
python -m venv .venv
source .venv/bin/activate   # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt

python -m src.main --data data/sample --out output
pytest -q
```

成功后会得到：

- `output/students/S001.md` … 每名学生一份 Markdown 学习材料
- `output/教师审核摘要.md` 供教师快速审核

可选参数：`--config config.yaml`、`--save-processed`（将清洗后的数据快照写入 `output/_processed/`）。

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

## 目录说明

```
personalized_engine/
├── README.md
├── requirements.txt
├── config.yaml
├── data/
│   ├── raw/            # 放置后续真实数据（不要写入姓名等私人信息）
│   ├── processed/      # 预留清洗结果
│   └── sample/         # 示例数据（已标注，可直接跑通）
├── src/
│   ├── data_loader.py
│   ├── cleaner.py
│   ├── profiler.py
│   ├── analyzer.py
│   ├── generator.py    # 含大模型预留接口
│   ├── exporter.py
│   └── main.py
├── tests/
└── output/             # 运行产出，已加入 .gitignore
```

## 隐私约定

- 输入与输出都只使用内部学号和年级、班级、选科、答题等学习字段；
- 不要把真实姓名、联系方式、家庭信息或其他无关私人数据放入本目录或提交到仓库；
- 教师审核摘要同样不含真实姓名。
