# 示例数据（SYNTHETIC） / Sample Data (SYNTHETIC)

> 语言说明 / Language note：中英双语，先中文后英文。 / Bilingual: Chinese first, then English.

本目录中的全部文件均为**虚构的示例数据**，只用于演示引擎能否跑通，**不是真实学生或真实考试**。

All files in this directory are **fictional sample data**, used only to demonstrate that the engine runs. They are **not real students or real exams**.

- 8 名内部学号（S001–S008），无真实姓名或其他私人信息 / 8 internal student IDs (S001–S008), with no real names or other private information
- 两种选科：物化生、史地生 / Two subject combinations: 物化生 (physics-chemistry-biology) and 史地生 (history-geography-biology)
- 若干场示例考试（物理 / 化学 / 生物 / 历史 / 地理，每科 1–3 场） / Several sample exams (physics / chemistry / biology / history / geography, 1–3 per subject)
- 含试卷原题与补充练习的小规模题库 / A small question bank with original exam questions and supplementary practice
- `checkins.csv`：2026-11-02 至 2026-11-08 的自习室签到示例（含少量缺勤） / `checkins.csv`: sample study-room check-ins from 2026-11-02 to 2026-11-08 (with a few absences)

直接运行 / Run directly:

```bash
python -m src.main --data data/sample --out output
# 或安装后 / or, after installing
eink-studyroom all --data data/sample --out output
```

接入真实数据时，请另放在 `data/raw/`，不要覆盖本目录，也不要写入姓名、联系方式等与学习无关的私人字段。

When using real data, put it separately in `data/raw/`; don't overwrite this directory, and don't include names, contact details or other private fields unrelated to learning.
