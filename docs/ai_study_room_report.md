# AI 自习室调研报告 / AI Study Room Research Report

> 语言说明 / Language note：本文中英双语，每段先中文后英文。 / This report is bilingual: each paragraph gives Chinese first, then English.

本文把「AI 自习室」理解为：线下座位与督学服务，叠加学情诊断、个性化练习和护眼阅读终端（本项目中为墨水屏），形成可运营的学习闭环。它与仓库中的个性化试卷与资料引擎、墨水屏下发方案是同一条产品线的不同层：引擎负责「每生一份材料」，自习室负责到馆安排、伴学和家长沟通，设备负责护眼阅读与低功耗更新。

This report defines an "AI study room" as offline seating and supervised-study services, combined with learning diagnosis, personalized practice and eye-friendly reading terminals (E-Ink in this project), forming an operable learning loop. It is a different layer of the same product line as the repository's personalized exam-and-materials engine and the E-Ink push plan: the engine produces "one material pack per student", the study room handles attendance arrangements, study coaching and parent communication, and the devices provide eye-friendly reading and low-power updates.

**数据与测算说明（请先阅读）：**

**Notes on data and estimates (please read first):**

- 下文市场规模、门店数量、客单价区间、续费率区间、启动成本和「百平百万」等表述，来自**行业公开报告与品牌宣传口径**（约 2024–2026 年），**未经本项目独立核实**，不能作为投资依据。决策前请自行向一手数据、当地成本和监管政策核实。
  Market size, store counts, price ranges, renewal-rate ranges, start-up costs and claims such as "a million yuan from a hundred square metres" below come from **public industry reports and brand marketing claims** (roughly 2024–2026), **have not been independently verified by this project**, and must not be used as a basis for investment. Before deciding, verify against primary data, local costs and regulations.
- 「单店财务模型」中的表格，由程序 `eink-studyroom finance` 根据 `personalized_engine/config.yaml` 里的**假设参数**计算，是情景测算，不是已发生的经营结果，更不是对收益的承诺。修改参数后重新运行即可复算。
  The tables in the "single-store financial model" are computed by `eink-studyroom finance` from the **assumed parameters** in `personalized_engine/config.yaml`. They are scenario estimates, not actual operating results, and certainly not a promise of returns. Change the parameters and rerun to recompute.
- 文中列出的品牌仅作**市场参考**，不表示本项目与其有合作、加盟或其他商业关系。
  Brands listed are **market references only** and do not imply any partnership, franchise or other business relationship with this project.
- 文档与程序输出均不使用真实个人姓名，学生侧只使用内部学号和学习相关字段。
  Neither the documents nor the program output use real personal names; on the student side, only internal student IDs and learning-related fields are used.

## 1. 市场概况 / 1. Market overview

AI 自习室是「双减」之后较快发展的一类业态，常见形态是：线下场地提供座位和伴学，再用学习机或本地系统做诊断、练习和督学。目标用户以小学至高中学生为主，付费主体是家长。一二线城市更看重可感知的学习效果，三四线城市往往同时看重托管便利和性价比。

AI study rooms are a fast-growing business format since China's "Double Reduction" policy. The typical form is an offline venue providing seats and study coaching, plus learning devices or a local system for diagnosis, practice and supervision. Target users are mainly primary to high-school students, and parents are the payers. Tier-1 and tier-2 cities care more about perceivable learning results; tier-3 and tier-4 cities often value both after-school supervision convenience and value for money.

公开报道中常见的数量级包括：2024 年相关市场规模约 350 亿元；有报告称 2025 年中国「AI + 教育」整体市场超过 700 亿元，AI 自习室是其中一块；截至 2024 年中，门店数量有「已超 5 万家」的说法。这些数字口径并不统一（有的含学习机硬件，有的含广义托管），且更新很快，只能当作数量级参考。

Orders of magnitude commonly seen in public reports include: a related market of about 35 billion yuan in 2024; one report says China's overall "AI + education" market exceeded 70 billion yuan in 2025, with AI study rooms as one part; and as of mid-2024 there were claims of "more than 50,000 stores". These figures use inconsistent definitions (some include learning-device hardware, some include broad after-school care) and change quickly, so treat them only as rough orders of magnitude.

行业已从早期铺店转向「门店仍在增加、单店盈利分化」的阶段。传统自习室容易陷入同质化、留存低；宣称的差异化通常是精准诊断、即时反馈和督学。也有案例宣传「学习效率提升约 40%」——这属于个案或广告表述，不能外推到所有门店或所有学生。

The industry has moved from early rapid store expansion to a stage of "store counts still growing, single-store profitability diverging". Traditional study rooms easily become homogeneous with low retention; claimed differentiators are usually precise diagnosis, instant feedback and supervision. Some cases advertise "about 40% higher learning efficiency" — these are individual cases or advertising claims and cannot be extrapolated to all stores or all students.

公开报道中较常被提及、可作**市场参考**的品牌包括赶考小状元、三陶教育、松鼠AI、好未来（彼芯）等。部分宣传强调「学习工场」模式，或给出三四线城市「百平年利润 80–120 万、6–12 个月回本」的案例。这些都是品牌宣传口径，**不表示本项目与上述品牌存在合作、加盟或其他商业关系**，也不能直接当作可复制的经营结果。

Brands frequently mentioned in public reports that can serve as **market references** include Gankao Xiaozhuangyuan (赶考小状元), Santao Education (三陶教育), Squirrel AI (松鼠AI) and TAL (好未来, Bixin/彼芯). Some marketing emphasizes a "learning workshop" model, or cites cases of "800k–1.2M yuan annual profit from 100 m², payback in 6–12 months" in tier-3/4 cities. These are all brand marketing claims, **do not imply any partnership, franchise or other business relationship between this project and those brands**, and cannot be taken as replicable operating results.

对本项目而言，真正可落地的差别不在「AI」这个词，而在：能否根据试卷和作答生成可审核的个性化材料、能否用墨水屏降低用眼负担，以及学生私人信息是否留在校内或店内本地处理。

For this project, the real, practical difference is not the word "AI" but whether it can generate reviewable personalized materials from exam papers and answers, whether E-Ink can reduce eye strain, and whether students' private information stays on campus or in-store and is processed locally.

## 2. 盈利模式 / 2. Business model

主流模式可以概括为「座位服务 + 学习内容/督学」，部分门店再叠加硬件。常见收入来源包括：

The mainstream model can be summarized as "seat service + learning content/supervision", with some stores adding hardware. Common revenue sources include:

- **座位 / 会员费**：按月或按学期收取机位和督导费用。宣传中的月费区间大约为 1200–2600 元，各地差异很大。
  **Seat / membership fees**: monthly or per-term fees for seats and supervision. Advertised monthly fees range roughly from 1,200 to 2,600 yuan, varying widely by region.
- **课程 / 提分包**：诊断之后的个性化练习或专项课包，有的宣传可占收入一半以上。
  **Courses / score-improvement packs**: personalized practice or topic packs after diagnosis; some marketing claims they make up more than half of revenue.
- **硬件销售或租赁**：学习机、平板或阅读器，既可能是引流，也可能是附加利润；本项目更强调墨水屏作为阅读和练习载体，而不是以硬件销售为中心。
  **Hardware sales or rental**: learning devices, tablets or readers, which may be a traffic driver or extra profit; this project emphasizes E-Ink as a reading and practice carrier rather than centring on hardware sales.
- **增值服务**：假期冲刺、资料、伴读或研学等。
  **Value-added services**: holiday intensive courses, materials, reading companionship, study tours, etc.

成本端主要是房租、店长和伴学师人力、装修与设备摊销，以及获客费用。轻资产加盟在宣传中较常见，但加盟费、系统使用费和物料费用需要单独核算，不能只看「零加盟费」口号。

Costs are mainly rent, labour for the store manager and study coaches, amortization of renovation and equipment, and customer acquisition. Asset-light franchising is common in marketing, but franchise fees, system fees and materials costs must be accounted for separately — don't rely on "zero franchise fee" slogans.

行业材料中常把盈利关键写成：

Industry materials often describe the key to profitability as:

> 座位利用率 × 客单价 × 续费率 − 固定成本（房租、人力、设备摊销）
>
> Seat utilization × price per customer × renewal rate − fixed costs (rent, labour, equipment amortization)

续费率被普遍视为比单纯拉新更重要的指标，宣传中常见 75%–85% 的区间。实际续费取决于效果是否可感知、交通是否便利、以及预收费和退费是否规范，不能预先假定落在该区间。

The renewal rate is widely seen as more important than pure new-customer acquisition, with 75%–85% commonly cited in marketing. Actual renewal depends on whether results are perceivable, whether transport is convenient, and whether prepayment and refunds are handled properly; you cannot assume in advance that it will fall in that range.

## 3. 单店财务模型（参数化测算） / 3. Single-store financial model (parameterized estimate)

本仓库用同一套公式做三种情景测算，避免把宣传案例直接写成「事实」。公式如下：

This repository uses one set of formulas for three scenario estimates, to avoid presenting marketing cases as "facts". The formulas are:

- **按利用率月营收** = 座位数 × 利用率 × 月费
  **Monthly revenue by utilization** = seats × utilization × monthly fee
- **稳态月营收（主口径）** = 座位数 × 利用率 × 续费率 × 月费
  **Steady-state monthly revenue (primary basis)** = seats × utilization × renewal rate × monthly fee
- **月固定成本** = 房租 + 人力 + 设备摊销
  **Monthly fixed cost** = rent + labour + equipment amortization
- **月利润** = 对应口径月营收 − 月固定成本
  **Monthly profit** = monthly revenue on the corresponding basis − monthly fixed cost
- **回本月数** = 启动成本 ÷ 月利润（月利润 ≤ 0 则标注「按当前假设无法回本」）
  **Payback months** = start-up cost ÷ monthly profit (if monthly profit ≤ 0, it is marked "no payback under current assumptions")

说明 / Notes:

- 「稳态」把续费率视为对在席学生持续付费的折减，是偏保守的近似，不是会计准则下的收入确认。
  "Steady state" treats the renewal rate as a discount on continued payment by enrolled students; it is a conservative approximation, not revenue recognition under accounting standards.
- 「按利用率」不折减续费，更接近只强调上座率的宣传算法。两列对照，是为了看出续费假设会在多大程度上改变回本周期。
  "By utilization" applies no renewal discount and is closer to marketing calculations that stress occupancy only. Comparing the two columns shows how much the renewal assumption changes the payback period.
- 未计入税费、获客费用、退费、空置装修期和设备二次投入。
  Taxes, customer acquisition, refunds, vacant renovation periods and equipment reinvestment are not included.
- 启动成本在公开宣传中常见 15–35 万元（含装修、设备和可能的加盟费用），下面三种情景分别取了偏高、居中、偏低的假设值。
  Start-up costs commonly cited in public marketing are 150k–350k yuan (including renovation, equipment and possible franchise fees); the three scenarios below use high, middle and low assumptions respectively.

默认假设（来自 `personalized_engine/config.yaml`，可修改后复算）：

Default assumptions (from `personalized_engine/config.yaml`; edit and recompute as needed):

| 情景 / Scenario | 座位数 / Seats | 利用率 / Utilization | 月费 / Monthly fee | 续费率 / Renewal | 房租 / Rent | 人力 / Labour | 设备摊销 / Equip. amort. | 启动成本 / Start-up cost |
|------|--------|--------|------|--------|------|------|----------|----------|
| 保守 / Conservative | 40 | 55% | 1,200 元 / CNY | 72% | 16,000 元 / CNY | 26,000 元 / CNY | 4,000 元 / CNY | 350,000 元 / CNY |
| 中性 / Neutral | 50 | 70% | 1,800 元 / CNY | 80% | 12,000 元 / CNY | 22,000 元 / CNY | 3,500 元 / CNY | 250,000 元 / CNY |
| 乐观 / Optimistic | 60 | 85% | 2,500 元 / CNY | 85% | 10,000 元 / CNY | 20,000 元 / CNY | 3,000 元 / CNY | 180,000 元 / CNY |

按当前默认假设，程序计算的结果如下（与 `eink-studyroom finance` 输出一致；若配置已改，以程序重新计算结果为准）：

With the current default assumptions, the program computes the following (consistent with `eink-studyroom finance` output; if the config has changed, the program's recomputed result prevails):

| 情景 / Scenario | 月成本 / Monthly cost | 按利用率月营收 / Revenue (utilization) | 按利用率月利润 / Profit (utilization) | 按利用率回本 / Payback (utilization) | 稳态月营收 / Steady revenue | 稳态月利润 / Steady profit | 稳态回本 / Steady payback | 稳态年利润 / Steady annual profit |
|------|--------|----------------|----------------|--------------|------------|------------|----------|------------|
| 保守 / Conservative | 46,000 元 | 26,400 元 | −19,600 元 | 按当前假设无法回本 / No payback under current assumptions | 19,008 元 | −26,992 元 | 按当前假设无法回本 / No payback under current assumptions | −323,904 元 |
| 中性 / Neutral | 37,500 元 | 63,000 元 | 25,500 元 | 9.8 个月 / months | 50,400 元 | 12,900 元 | 19.4 个月 / months | 154,800 元 |
| 乐观 / Optimistic | 33,000 元 | 127,500 元 | 94,500 元 | 1.9 个月 / months | 108,375 元 | 75,375 元 | 2.4 个月 / months | 904,500 元 |

（金额单位：元 / Amounts in CNY）

可以这样读这张表：

How to read this table:

- **保守情景**在两种口径下都不能覆盖固定成本。利用率偏低、客单偏低、房租和人力偏高时，自习室会先变成「坐不满的房间」，而不是自动盈利的门店。
  The **conservative scenario** cannot cover fixed costs on either basis. With low utilization, low prices and high rent and labour, a study room first becomes "a room that can't fill its seats", not a store that automatically makes money.
- **中性情景**若只按利用率看，回本约 10 个月，接近部分宣传中的「6–12 个月」；一旦按续费折减，回本会被拉长到约 19 个月。宣传周期往往更接近未充分压力测试续费的算法。
  In the **neutral scenario**, looking at utilization alone gives payback in about 10 months, close to the "6–12 months" in some marketing; once the renewal discount is applied, payback stretches to about 19 months. Advertised periods tend to resemble calculations that haven't stress-tested renewals.
- **乐观情景**的年利润会落到部分品牌宣传的「百平年利润约 80–120 万」附近，回本也只有数月。这需要同时成立的高上座、高客单、高续费和相对低的租金人力。它适合用来理解宣传数字是如何被做出来的，不适合直接当成可复制目标。
  The **optimistic scenario**'s annual profit lands near some brands' claim of "about 800k–1.2M yuan annual profit from 100 m²", with payback in just a few months. This requires high occupancy, high prices, high renewals and relatively low rent and labour all at once. It is useful for understanding how marketing figures are produced, not as a replicable target.

公开材料中还有「成功案例年营收 120–200 万元」「理想回本 6–12 个月」等说法。把中性、乐观情景与这些口径对照即可发现：它们高度依赖选址、招生和续费，而不是「开了 AI 自习室就会如此」。运行以下命令可复现或改参后重算：

Public materials also mention "successful cases with 1.2–2M yuan annual revenue" and "ideal payback in 6–12 months". Comparing the neutral and optimistic scenarios with these claims shows they depend heavily on location, enrolment and renewals — not "open an AI study room and it will happen". Run the following to reproduce or recompute with new parameters:

```bash
cd personalized_engine
eink-studyroom finance --out output
```

## 4. 营销推广 / 4. Marketing and promotion

获客仍以本地化、口碑和转介绍为主，线上内容更多是辅助信任，而不是跨区域投放。常见做法如下。

Customer acquisition still relies mainly on local presence, word of mouth and referrals; online content mostly supports trust rather than cross-region advertising. Common practices:

- **地推**：在学校放学时段发放短期体验（例如低价体验若干天），把「托管看管 + 当场可问」说清楚，避免只谈抽象的 AI。
  **Street promotion**: hand out short trials at school dismissal time (e.g. a few low-cost trial days), clearly explaining "supervised care + ask questions on the spot", and avoid talking only about abstract AI.
- **社群运营**：用家长群同步可核验的学情（出勤、薄弱知识点、本周练习），定期开简短说明会。展示材料时只用学号或经授权的匿名案例，不要在群里传播完整私人信息。
  **Community operations**: share verifiable learning status in parent groups (attendance, weak knowledge points, this week's practice) and hold short briefings regularly. Use only student IDs or authorized anonymized cases when showing materials; never spread full private information in groups.
- **转介绍**：老带新双方给予课时或抵扣，规则公开、可兑现，避免把转介绍做成隐性推销。
  **Referrals**: give both the referrer and the new student class hours or discounts, with public, honourable rules; don't turn referrals into hidden sales pressure.
- **内容营销**：用短视频或图文展示「一份个性化材料如何生成、如何在墨水屏上阅读」，少用无法核验的「从 xx 分到 xx 分」话术。
  **Content marketing**: use short videos or posts to show "how a personalized material pack is generated and read on E-Ink", and avoid unverifiable "from xx points to xx points" claims.
- **免费诊断**：用校内或店内测验做引流，诊断结果应当能对上试卷和作答，而不是只出一份漂亮报告。
  **Free diagnosis**: use school or in-store tests to attract customers; diagnosis results should match the exam papers and answers, not just produce a pretty report.
- **异业合作**：与社区书店、文体商店等互放体验名额，选择与学习场景相关、不会造成信息滥用的合作方。
  **Cross-industry cooperation**: exchange trial slots with community bookshops, stationery and sports stores, etc., choosing partners relevant to learning that won't misuse information.

本项目可强调、且应当能被核验的两个差异点：

Two differentiators this project can emphasize, and that should be verifiable:

1. **墨水屏护眼**：练习和阅读以下发到 E-Ink 设备为主，减少长时间亮背光屏幕，接近纸质阅读体验，同时免除每周打印。
   **Eye-friendly E-Ink**: practice and reading are mainly pushed to E-Ink devices, reducing long periods on backlit screens, close to a paper reading experience, and eliminating weekly printing.
2. **每生一份个性化材料**：依据考试试卷、逐题作答和选科组合生成错题重练与分层资料，并附教师或伴学师审核摘要，而不是全班同一张卷。
   **One personalized pack per student**: mistake re-practice and tiered materials generated from exam papers, per-question answers and subject combinations, with a teacher or study-coach review summary, instead of the same paper for the whole class.

体验转化、首月招生规模等案例数字差异极大，本文不引用无法核对来源的「首月上百人、转化率 30%+」作为可预期结果。更稳妥的做法是：先用本仓库的示例数据跑通「诊断 → 材料 → 场次 → 周报」闭环，再用本地真实成本重做财务测算，再决定是否小规模试点。

Case figures for trial conversion and first-month enrolment vary enormously; this report does not cite unverifiable claims like "hundreds of students in the first month, 30%+ conversion" as expected results. A safer approach: first run the "diagnosis → materials → sessions → weekly report" loop with this repository's sample data, then redo the financial estimate with real local costs, and only then decide on a small-scale pilot.

## 5. 风险与合规 / 5. Risks and compliance

- **高扩张、低盈利**：门店数量增加并不等于单店赚钱。招生不及预期、续费下滑时，回本周期会明显长于宣传。上一节的保守情景就是用来提醒这一点。
  **High expansion, low profitability**: more stores does not mean each store makes money. When enrolment falls short or renewals drop, payback takes much longer than advertised. The conservative scenario above is a reminder of this.
- **预收费监管**：预收学费、会员费通常有周期和额度限制，需保留可退费路径和书面告知。不要用「一次收一年」来美化现金流。具体以经营所在地当时有效的规定为准。
  **Prepayment regulation**: prepaid tuition and membership fees usually have period and amount limits; keep a refund path and written notice. Don't dress up cash flow by "collecting a full year at once". Local regulations in force at the time apply.
- **数据安全**：学情数据、作答记录和到馆记录应本地或校内处理，传输与存放要有权限控制。本引擎默认不调用外部 API；若日后接入校内部署的模型，仍应避免把原始学生数据送到校外。
  **Data security**: learning data, answer records and attendance records should be processed locally or on campus, with access control for transfer and storage. This engine calls no external APIs by default; if a campus-hosted model is connected later, raw student data should still never be sent off campus.
- **学生隐私不出校**：只保留学号、年级、班级、选科、答题和出勤等学习字段；姓名、电话、证件号、家庭信息等与学习无关的私人数据不得进入本系统，也不得写入周报或提交到公开仓库。家长沟通材料同样只使用学习字段。
  **Student privacy stays on campus**: keep only learning fields such as student ID, grade, class, subject combination, answers and attendance; private data unrelated to learning — names, phone numbers, ID numbers, family information — must not enter this system, be written into weekly reports, or be committed to a public repository. Parent communication materials likewise use learning fields only.
- **教育资质与效果边界**：涉及学科培训或托管，需核对本地区办学或培训资质。提分取决于学生投入、材料质量和伴学，不是所有学生都会显著进步，宣传中必须留有余地。
  **Educational licensing and limits on results**: for subject tutoring or after-school care, check local school-running or training licences. Score improvement depends on student effort, material quality and coaching; not every student will improve significantly, so marketing must leave room for that.
- **同质化与成本**：设备差异会很快被赶上，最终仍是服务、口碑和选址的竞争。一二线房租和人力更高，不能直接套用三四线宣传案例。
  **Homogenization and cost**: device differences are quickly caught up with; ultimately the competition is on service, reputation and location. Rent and labour are higher in tier-1/2 cities, so tier-3/4 marketing cases cannot be applied directly.

## 6. 建议 / 6. Recommendations

- **先验证闭环，再谈铺店**：用本仓库程序在小样本上跑通个性化材料、座位场次、签到周报和财务测算，再考虑场地投入。
  **Validate the loop before expanding**: use this repository's program on a small sample to run personalized materials, seat sessions, check-in weekly reports and the financial estimate before investing in a venue.
- **选址重于概念**：靠近学校或学生密度高的社区，交通和放学动线要比「AI」口号更重要。
  **Location over concept**: be near schools or communities dense with students; transport and after-school routes matter more than the "AI" slogan.
- **财务按保守情景留出资金**：即使中性情景看起来可做，也应按无法快速回本的情况预留数月运营资金，不要按乐观情景排扩张计划。
  **Reserve funds per the conservative scenario**: even if the neutral scenario looks viable, set aside several months of operating funds assuming no quick payback, and never plan expansion on the optimistic scenario.
- **把可核验的效果当作产品**：学情周报、错题重练和教师审核摘要应能被家长和教师看懂；不要用无法复核的分数故事替代过程数据。
  **Make verifiable results the product**: weekly learning reports, mistake re-practice and teacher review summaries should be understandable to parents and teachers; don't replace process data with unverifiable score stories.
- **合规前置**：预收费规则、退费流程、数据存放位置和隐私字段清单要在招生前写清。
  **Compliance first**: write down prepayment rules, refund procedures, data storage locations and the list of privacy fields before enrolling students.
- **品牌宣传只作对照**：可将市场中的活跃品牌当作竞争参考，但不把对方的利润海报写进自己的计划书。
  **Use brand marketing only for comparison**: active brands can serve as competitive references, but don't put their profit posters into your own business plan.

**总结**：AI 自习室对应的是真实存在的托管和个性化练习需求，但行业竞争已经加剧，盈利高度分化。对本项目，更稳妥的定位是：以墨水屏为阅读载体、以规则引擎生成可审核的每生材料、以本地数据保证隐私不出校，并用可改参数的单店测算约束扩张预期。是否开店，取决于选址、成本和续费的本地核实，而不是市场口号。

**Summary**: AI study rooms answer a real demand for after-school care and personalized practice, but competition has intensified and profitability varies widely. For this project, the safer positioning is: E-Ink as the reading carrier, a rule engine generating reviewable per-student materials, local data keeping privacy on campus, and an adjustable single-store estimate to restrain expansion expectations. Whether to open a store depends on local verification of location, costs and renewals, not market slogans.

相关文档与程序 / Related documents and programs:

- [从纸质个性化材料到墨水屏读书器的改进方案 / From personalized paper materials to E-Ink readers](personalized_eink_learning.md)
- [个性化引擎与 AI 自习室程序说明 / Personalized engine and AI study-room program guide](../personalized_engine/README.md)
- 命令 / Commands：`eink-studyroom generate` / `report` / `finance` / `all`
