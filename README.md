# 5GEinkStudyMachineAndPushMethod

> 语言说明 / Language note：本仓库全部文档、代码注释、命令行提示和生成材料均为中英双语，一般先中文后英文。 / All documentation, code comments, CLI messages and generated materials in this repository are bilingual (Chinese–English), usually Chinese first, then English.

一种基于5G架构的穿戴式护眼墨水屏学习机及基于深度学习的教育推送算法实现

A wearable, eye-friendly E-Ink learning device based on 5G architecture, and an implementation of a deep-learning-based educational content push algorithm.

## 项目定位 / Project positioning

随着AI发展，针对每个学生的实体素质教育变得更加重要。本项目把传统“AI分析学情 → 打印每生一份纸质个性化材料 → 教师审核引导”的模式，改进为**墨水屏读书器**载体：

As AI develops, hands-on, well-rounded education tailored to each student becomes more important. This project upgrades the traditional model of "AI analyses learning data → prints one personalized paper pack per student → teachers review and guide" into an **E-Ink reader** carrier:

- 保护视力（E-Ink 护眼） / Protects eyesight (eye-friendly E-Ink)
- 减少屏幕依赖与运维成本 / Reduces screen dependence and operating costs
- 支持校内外无设备学生平等使用 / Lets students without their own devices, on or off campus, use it equally
- 内容可即时更新、可反馈、可迭代 / Content can be updated instantly, receive feedback, and iterate

核心目标：用深度学习算法实现“因材施教”的教育资源推送与反馈处理，形成一套可落地的个性化学习闭环。

Core goal: use deep-learning algorithms to push educational resources and process feedback in a "teach each student according to their aptitude" way, forming a practical, closed personalized-learning loop.

## 核心要素 / Core elements

1. **载体**：穿戴式 / 手持小型设备（手表、校牌、校卡、饭卡形态或独立阅读器），搭载彩色或黑白 E-Ink 墨水屏。
   **Carrier**: wearable / small handheld devices (watch, school badge, school card, meal-card form factors, or a standalone reader) with a colour or black-and-white E-Ink screen.
2. **网络**：5G 或物联网架构，支持低功耗、按需同步。
   **Network**: 5G or IoT architecture, supporting low-power, on-demand synchronization.
3. **学习场景**：主要用于阅读、知识增补、分层练习与错题巩固。也可嵌入 AI 自习室：伴学师按薄弱科目安排座位与场次，材料下发到墨水屏，周报只含学习字段。
   **Learning scenarios**: mainly reading, knowledge supplementation, tiered practice and consolidating mistakes. It can also be embedded in an AI study room: study coaches assign seats and sessions by weak subject, materials are pushed to the E-Ink screens, and weekly reports contain learning fields only.
4. **算法目标**：寻找一种可行的深度学习推送与反馈算法，逐步逼近“解决学生学习的终极算法”。
   **Algorithm goal**: find a workable deep-learning push-and-feedback algorithm, gradually approaching "the ultimate algorithm for solving student learning".
5. **教学组织 / Teaching organization**：
   - 小班（25–30人）：使用墨水屏个性化材料进行针对性辅导、项目研讨。
     Small classes (25–30 students): targeted tutoring and project discussions using personalized E-Ink materials.
   - 大班：共性内容讲授。
     Large classes: lectures on common content.
   - 教师聚焦概念建构与价值引导，AI承担可复制的内容生成与初稿。
     Teachers focus on concept building and value guidance; AI handles reproducible content generation and first drafts.

## AI 自习室 / AI study room

本仓库把墨水屏个性化学习与 AI 自习室运营放在同一套程序里：线下座位和督学服务，叠加「每生一份材料」和护眼阅读终端。详细调研（市场概况、盈利模式、参数化单店测算、营销、风险与建议）见：

This repository puts E-Ink personalized learning and AI study-room operations into one program: offline seats and supervised-study services, plus "one material pack per student" and eye-friendly reading terminals. For the detailed research (market overview, business model, parameterized single-store estimate, marketing, risks and recommendations), see:

- [`docs/ai_study_room_report.md`](docs/ai_study_room_report.md)

其中单店财务表由程序按 `personalized_engine/config.yaml` 的假设参数计算，不是已核实的经营事实。市场数据来自行业公开报告与品牌宣传口径，未经独立核实，投资前需自行核实。文中提及的品牌只作市场参考，不表示存在合作关系。

The single-store financial table is computed by the program from the assumed parameters in `personalized_engine/config.yaml`; it is not verified operating data. Market figures come from public industry reports and brand marketing claims and have not been independently verified; verify them yourself before investing. Brands mentioned are market references only and do not imply any partnership.

### 安装与运行 / Install and run

```bash
cd personalized_engine
python -m venv .venv
source .venv/bin/activate   # Windows 使用 / on Windows use: .venv\Scripts\activate
pip install -e ".[dev]"

eink-studyroom generate --data data/sample --out output
eink-studyroom report --data data/sample --out output
eink-studyroom finance --out output
eink-studyroom all --data data/sample --out output
pytest -q
```

不安装包时，原入口仍然可用：

Without installing the package, the original entry point still works:

```bash
cd personalized_engine
pip install -r requirements.txt
python -m src.main --data data/sample --out output
```

示例数据在 `personalized_engine/data/sample/`（虚构数据，仅供演示）。真实学生数据应放在 `data/raw/`，不要写入姓名等私人信息，也不要提交到仓库。

Sample data is in `personalized_engine/data/sample/` (fictional, for demonstration only). Real student data belongs in `data/raw/`; do not include names or other private information, and never commit it to the repository.

## 与新建校区AI建设的衔接 / Integration with AI construction on a new campus

本项目可直接嵌入新建高中校区“五层一体”架构中的应用层：

This project can be embedded directly into the application layer of a new high-school campus's "five-layer integrated" architecture:

- 学情数据由AI中台汇总 / Learning data is aggregated by the AI middle platform
- 本地算力生成个性化内容 / Local computing power generates personalized content
- 通过5G/物联网下发到学生墨水屏设备 / Content is pushed to students' E-Ink devices over 5G/IoT
- 教师在小班审核、引导、补充 / Teachers review, guide and supplement in small classes
- 学生反馈数据回传，持续优化推送模型 / Student feedback flows back to continuously optimize the push model
- 若用于校内或社区自习室，座位场次与学情周报也在本地生成，学生隐私不出校 / If used in a school or community study room, seat sessions and weekly learning reports are also generated locally, so student privacy never leaves the school

## 目录规划（逐步完善） / Directory plan (being built out)

- [`docs/personalized_eink_learning.md`](docs/personalized_eink_learning.md)：从纸质个性化材料到墨水屏读书器的改进方案 / The upgrade plan from personalized paper materials to E-Ink readers
- [`docs/ai_study_room_report.md`](docs/ai_study_room_report.md)：AI 自习室调研报告（市场、盈利、单店测算、营销、风险与建议） / AI study-room research report (market, business model, single-store estimate, marketing, risks and recommendations)
- [`personalized_engine/`](personalized_engine/)：个性化试卷与资料引擎，以及 AI 自习室 CLI（`eink-studyroom`） / Personalized exam-and-materials engine, plus the AI study-room CLI (`eink-studyroom`)
- `docs/`：详细方案、算法思路、硬件选型、教学组织流程 / Detailed plans, algorithm ideas, hardware selection, teaching-organization workflow
- `simulation/`：推送算法仿真与学情反馈模拟 / Push-algorithm simulation and learning-feedback simulation
- `hardware/`：墨水屏设备接口与低功耗同步协议说明 / E-Ink device interfaces and low-power sync protocol notes

## 原始构想（2019） / Original concept (2019)

1、一种基于5G架构的穿戴式护眼墨水屏学习机及基于深度学习的教育推送算法实现  
1. A wearable, eye-friendly E-Ink learning device based on 5G architecture, and an implementation of a deep-learning-based educational push algorithm  
2、5G架构或者物联网架构  
2. 5G architecture or IoT architecture  
3、穿戴式如手表、校牌、校卡、饭卡、手持小型设备等  
3. Wearables such as watches, school badges, school cards, meal cards, small handheld devices, etc.  
4、护眼eink墨水屏包括：彩色和黑白  
4. Eye-friendly E-Ink screens, both colour and black-and-white  
5、学习机：主要用于学习和读书增加知识，结合深度学习算法进行因材施教教育  
5. Learning device: mainly for studying and reading to gain knowledge, combined with deep-learning algorithms to teach each student according to aptitude  
6、采用深度学习算法，寻找一种可行的算法进行推送教育资源和处理反馈资源  
6. Use deep-learning algorithms to find a workable algorithm for pushing educational resources and processing feedback  
7、算法：一种可以解决学生学习的终极算法  
7. Algorithm: an ultimate algorithm that can solve student learning  

## 下一步 / Next steps

欢迎补充具体算法实现、硬件对接代码或教学试点数据。接入真实学情时请只提供学习相关字段，不要提交私人信息。

Contributions of concrete algorithm implementations, hardware integration code or teaching-pilot data are welcome. When connecting real learning data, provide learning-related fields only and never commit private information.
