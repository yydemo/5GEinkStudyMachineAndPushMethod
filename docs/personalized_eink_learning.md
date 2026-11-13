# 从纸质个性化材料到墨水屏读书器的改进方案 / From Personalized Paper Materials to E-Ink Readers: Upgrade Plan

> 语言说明 / Language note：本文中英双语，先中文后英文。 / This document is bilingual: Chinese first, then English.

## 原有模式（论文实践） / Original model (from the paper's practice)

1. AI依托学情数据为每位学生生成分层学案、错题包、阅读清单。
   Based on learning data, AI generates tiered study plans, mistake packs and reading lists for each student.
2. 打印成纸质材料分发。
   These are printed and distributed as paper materials.
3. 小班使用个性化纸质包进行针对性辅导。
   Small classes use the personalized paper packs for targeted tutoring.
4. 大班讲授共性内容。
   Large classes are taught common content.
5. 教师审核AI初稿，聚焦概念建构与价值引导。
   Teachers review AI first drafts and focus on concept building and value guidance.

优点：减少屏幕时间、保护视力、校外学生也能使用。  
Strengths: less screen time, protects eyesight, and students off campus can use it too.  
不足：打印成本高、内容更新慢、无法即时反馈、无法动态调整。  
Weaknesses: high printing cost, slow content updates, no instant feedback, no dynamic adjustment.

## 改进后的墨水屏模式 / The upgraded E-Ink model

| 环节 / Stage | 纸质方案 / Paper approach | 墨水屏方案 / E-Ink approach |
|------|----------|------------|
| 内容生成 / Content generation | AI生成后打印 / Printed after AI generation | AI生成后通过5G/物联网下发到设备 / Pushed to devices over 5G/IoT after AI generation |
| 分发 / Distribution | 人工打印分发 / Printed and handed out manually | 设备自动同步（低功耗） / Automatic device sync (low power) |
| 使用场景 / Usage scenario | 小班纸质包 / Paper packs in small classes | 小班墨水屏阅读 + 即时批注/反馈 / E-Ink reading in small classes + instant annotation/feedback |
| 更新频率 / Update frequency | 按周/单元 / Weekly / per unit | 可按课、按天、按反馈即时更新 / Per lesson, per day, or instantly based on feedback |
| 反馈闭环 / Feedback loop | 人工收集 / Collected manually | 设备端操作数据自动回传 / Device interaction data returned automatically |
| 视力保护 / Eye protection | 纸质 / Paper | E-Ink 护眼，接近纸质 / Eye-friendly E-Ink, close to paper |
| 成本 / Cost | 持续打印耗材 / Ongoing printing consumables | 一次硬件投入，长期低运维 / One-off hardware investment, low long-term maintenance |

## 推荐设备形态 / Recommended device form factors

- 独立手持阅读器（优先） / Standalone handheld reader (preferred)
- 校牌/校卡形态（轻量） / School badge / school card form (lightweight)
- 手表形态（极简信息） / Watch form (minimal information)
- 支持彩色与黑白 E-Ink / Supports colour and black-and-white E-Ink

## 推送算法初步思路 / Initial ideas for the push algorithm

1. 输入：学情数据（错题、掌握度、阅读进度、教师标注）
   Input: learning data (mistakes, mastery, reading progress, teacher annotations)
2. 模型：推荐系统 + 知识图谱 + 大模型内容生成
   Model: recommender system + knowledge graph + large-model content generation
3. 输出：个性化内容包（阅读材料 + 练习 + 错题重练）
   Output: personalized content packs (reading materials + exercises + mistake re-practice)
4. 反馈：阅读时长、完成率、正确率、教师批注 → 更新学生画像
   Feedback: reading time, completion rate, accuracy, teacher annotations → update the student profile
5. 目标：逐步形成可解释、可干预的“终极学习算法”
   Goal: gradually build an explainable, steerable "ultimate learning algorithm"

## 与新建校区落地建议 / Recommendations for deployment on a new campus

- 规划阶段预留墨水屏充电与同步点（教室/宿舍） / Reserve E-Ink charging and sync points during planning (classrooms/dorms)
- 小班空间按25–30人配置，方便设备使用与教师引导 / Size small-class rooms for 25–30 students to ease device use and teacher guidance
- 大班仍以讲授为主，墨水屏作为课后/课前个性化补充 / Large classes remain lecture-based, with E-Ink as personalized pre-/after-class supplements
- 数据不出校，内容生成在本地AI中台完成 / Data stays on campus; content is generated on the local AI middle platform

此方案保留了论文中“减负而非替代”“教师回归引导者”的核心取向，同时解决了纸质方案的更新与反馈痛点。

This plan keeps the paper's core orientation of "reducing burden rather than replacing teachers" and "teachers returning to the role of guides", while solving the update and feedback pain points of the paper approach.

相关文档：[AI 自习室调研报告](ai_study_room_report.md)。 / Related document: [AI study-room research report](ai_study_room_report.md).
