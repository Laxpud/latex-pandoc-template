# 参考文献条目草案

本文档用于规划 `reference.bib` 的示例条目。目标不是收录真实学术文献，而是围绕影音、游戏、动画、电影和小说作品，虚构一组“半严肃、半荒诞”的参考文献，使模板在演示时更有传播性，同时覆盖 `gbt7714.bst` 支持的主要 BibTeX 条目类型。

## 设计原则

- 条目应像作品世界观内部真实存在的文献、报告、档案、标准、专利或数据资源。
- 标题可以严肃，研究对象可以离谱；不要写成单纯的梗。
- 英文条目占多数，中文条目约占四分之一，用于测试中英文混排。
- 每类条目尽量触发不同字段：作者、机构、学校、编辑、译者、卷期、页码、编号、URL、访问日期、专利号、报告号等。
- 作者、编辑和机构优先使用作品内比较被公众熟知的角色或组织，让条目像是从世界观内部自然长出来的。
- 部分条目刻意设置 4 位及以上作者，用于测试参考文献样式中的“等”和 “et al.” 省略规则。
- 同一作品可以出现多种文献形态，但不宜让某一作品垄断整个参考文献库。

## 类型语气约束

- `article`：必须像正式期刊论文，题目应有明确研究对象、方法或实验条件，适合写卷、期、页码和 DOI。
- `conference` / `inproceedings`：必须像会议论文，会议本身要符合世界观，题目则仍然保持科研或技术评审语气。
- `proceedings`：应是整本会议论文集，不是其中一篇文章。
- `book` / `monograph`：应像系统性专著，题目可以宏大，但要有稳定学术主题。
- `booklet`：应像薄册子、内部规程、社团说明，不宜写成正式论文。
- `manual`：应像操作、维护、装配或应急手册。
- `newspaper`：必须是新闻报道或特刊报道，标题要像媒体写法，而不是论文题目。
- `dataset` / `database` / `software` / `standard`：要像可复用的数据、知识库、软件或规范文件，突出版本、机构和访问字段。
- `unpublished`：应像未公开笔记、草案、临时处置方案或内部备忘录。

## 类型分配草案

| BibTeX 类型 | 作品 | 拟作者/机构 | 语言 | 草案题目与方向 | 测试重点 |
| --- | --- | --- | --- | --- | --- |
| `article` | *Cyberpunk 2077* | Alt Cunningham; T-Bug | English | 《基于皮层改造芯片侧信道回波的入侵可观测性分析与低延迟神经干扰研究》：把黑客入侵写成信号处理问题，重点测试义体芯片、神经噪声、ICE 反馈和毫秒级延迟之间的耦合。 | `journal`, `volume`, `number`, `pages`, `doi` |
| `article` | 《三体》 | 王淼 | 中文 | 《基于飞刃纳米材料的高张力钢结构准静态切割性能分析与多层甲板干扰实验》：表面是材料力学论文，实验对象只写“多层船用钢结构样件”，让古筝计划的暗示藏在题目和数据里。 | 中文作者、中文期刊、页码 |
| `archive` | 《黑神话：悟空》 | 天庭巡察司; 土地庙案牍房; 二郎显圣真君 | 中文 | 《孙悟空六根封存案牍、妖王受领文书与天庭责任切割批注汇编》：一组天庭内部归档材料，核心不是“六根如何保存”，而是各级仙官如何把残躯处置的后果拆分、外包并转写为妖王自愿受领，从而在档案层面完成责任规避。 | `title`, `organization`, `address`, `year`, `url` |
| `book` | *Dark Souls* | Big Hat Logan | English | 《初火余辉条件下灵魂能级衰减、空洞化动力学与王器再点火阈值》：像一本洛德兰自然哲学专著，把传火、灵魂和不死人循环写成热力学与宗教制度的混合模型。 | `publisher`, `address`, `edition` |
| `booklet` | 《轻音少女》 | 琴吹紬; 平泽唯; 秋山澪; 田井中律; 中野梓 | 中文 | 《放课后 Tea Time 茶点制备、分配与练习室清洁规程》：一本社团内部小册子，用极其正式的语气规定红茶温度、蛋糕切分、乐器避让和排练前后桌面复位流程；五人作者可测试中文“等”。 | `howpublished`, `address`, `year` |
| `collection` | *Delicious in Dungeon* | Senshi; Laios Touden; Marcille Donato; Chilchuck Tims; Namari | English | 《地下城可食魔物的热处理窗口、毒性分级与生态采收论文集》：整本文集由多名迷宫实践者编辑，章节分别讨论毒理、可食部位、热处理、生态采收和队伍补给。 | `editor`, `publisher`, `series` |
| `conference` | 《黑神话：悟空》 | 二郎显圣真君; 太上老君; 黄眉; 牛魔王 | 中文 | 《孙悟空六根分离封存过程中的权属分配、容器稳定性与再感应风险评估》：上清天庭灵蕴封存与妖族治理联合会议论文。时间线限定在大圣残躯处置之后、天命人登场之前，讨论各方如何处置六根遗存。 | `booktitle`, `organization`, `address` |
| `database` | *Elden Ring* | Gideon Ofnir | English | 《交界地遗物来源、卢恩铭文与半神亲缘声明的冲突数据库》：用“百智爵士”的口吻维护一套越查越乱的知识库，专门记录黄金律法叙事中的矛盾时间戳。 | `url`, `urldate`, `organization` |
| `dataset` | *One Punch Man* | Genos; Child Emperor; Metal Knight; Dr. Kuseno; Hero Association | English | 《英雄协会灾害等级修订、城区损伤与 S 级响应延迟数据集》：把怪人灾害写成城市韧性数据，字段包括灾害评级漂移、建筑损失、英雄到场延迟和战后宣传修正；多作者可测试 “et al.”。 | `version`, `institution`, `url` 等普通字段 |
| `electronic` | *Cyberpunk 2077* | Judy Alvarez | English | 《超梦记录中触觉通道压缩伪影、情绪同步误差与非法分发链路电子档案》：以超梦编辑师视角记录感官数据如何被压缩、篡改、传播和二次售卖。 | `medium`, `url`, `urldate` |
| `inbook` | *The Wandering Earth* | 图恒宇; MOSS | English | 《月球发动机相位误差、数字生命备份延迟与全球点火协议》中的一章：把数字生命计划和行星发动机控制问题放在同一本工程史里，突出“延迟”如何同时是计算问题和伦理问题。 | `chapter`, `pages`, `publisher` |
| `incollection` | *Frieren: Beyond Journey's End* | Frieren; Fern | English | 《长寿种族记忆误差、低频哀悼行为与民用魔法目录维护》：收录在记忆工程文集中的章节，把芙莉莲的旅行写成跨世代数据采样和魔法工艺档案维护。 | `booktitle`, `editor`, `pages` |
| `inproceedings` | *Death Stranding* | Sam Porter Bridges; Fragile | English | 《时间雨暴露条件下末端配送路径的时变退化模型与手性网络信任权重修正》：物流会议论文，讨论地形、货损、连接等级和派送员声誉如何共同影响路由。 | `booktitle`, `pages`, `doi` |
| `manual` | *Sekiro: Shadows Die Twice* | 佛雕师; 永真 | English | 《忍义手模块化机关的维护、忍具载荷匹配与炎症后组织恢复手册》：把机关伞、爆竹、斧、火吹筒写成可维护机械系统，同时塞进药理与截肢康复。 | `organization`, `edition`, `number` |
| `map` | 《迷宫饭》 | 森西; 玛露希尔 | 中文 | 《黄金乡地下迷宫可食魔物分布、迁徙季节与热处理风险图》：地图不仅标注路径，还标注可食部位、烹调前处理、毒性阈值和不建议扎营的生态节点。 | `publisher`, `address`, `medium` |
| `mastersthesis` | *Bocchi the Rock!* | Hitori Gotoh | English | 《低信噪比舞台环境中个体焦虑反馈、吉他失真参数与小型乐队同步性的相关性研究》：一篇看似音频工程，实则把社恐反应严肃写进舞台声学模型的硕士论文。 | `school`, `address`, `year` |
| `misc` | *Armored Core VI* | Handler Walter; Ayre | English | 《卢比孔独立佣兵任务板残片、珂若尔回声注记与委托目标漂移记录》：零散材料，适合测试 `misc` 的不规则来源和 `note` 字段。 | `howpublished`, `note` |
| `monograph` | 《诡秘之主》 | 克莱恩·莫雷蒂 | 中文 | 《灰雾占卜干扰条件下非凡事件溯源、风险分级与值夜者行动决策》：一部廷根值夜者内部专著，核心问题是如何在占卜结果不稳定、信息被污染且现场证据不足时，把非凡事件从“巧合”识别为可处置案件。 | `publisher`, `address`, `year` |
| `newspaper` | *Tamako Market* | Usagiyama Shopping District News | English | 《年糕节前夜蒸笼蒸汽管线短时故障，兔山商店街自治会称供应不受影响》：必须写成新闻报道，包含时间、地点、事件、受访方和轻微夸张的街区公共事务感。 | `journal`, `date`, `pages` |
| `online` | *K-On!* | Azusa Nakano | English | 《樱高轻音部设备谱系、放大器设置与学园祭录音版本差异在线考据》：粉丝页面式在线资源，但内容像设备溯源和现场声学复现指南。 | `url`, `urldate`, `language` |
| `patent` | *Lord of the Mysteries* | Roselle Gustav | English | 《一种面向异界既有技术方案的本地化转译、权利要求重组与神秘学负反馈规避方法》：罗塞尔式“发明专利”，核心是把穿越前的旧世界知识包装成本世界可生产、可宣称原创、且尽量不触发神秘学反噬的技术方案。 | `number`, `date`, `author` 或 `organization` 模拟权利人 |
| `periodical` | 《败犬女主太多了！》 | 温水和彦; 丰桥青春观察编辑部 | 中文 | 《丰桥青春观察：校园关系网络、告白失败率与便当交换行为的连续观测专号》：把恋爱喜剧写成社会网络观测月刊，适合测试期刊型整体条目。 | `title`, `year`, `number`, `publisher` |
| `phdthesis` | *Elden Ring* | Sorceress Sellen | English | 《辉石晶核中原初流的相干激发、意识转写与学院伦理边界研究》：雷亚卢卡利亚学院博士论文，把辉石魔法写成晶体介质、意识载荷和禁忌实验之间的基础研究问题。 | `school`, `address`, `year` |
| `proceedings` | *Elden Ring* | Ranni the Witch; Gideon Ofnir | English | 《第一届罗德尔赐福测量、星月相位与恶兆分类联合会议论文集》：会议论文集，各派试图把神学现象标准化为可测量参数，当然越测越政治。 | `editor`, `publisher`, `address` |
| `software` | *Armored Core VI* | ALLMIND; Handler Walter; Ayre; Cinder Carla; V.IV Rusty | English | 《ALLMIND ArenaBench：AC 零件组合仿真测试、训练场目标响应与机体适配性评估软件》：对应游戏里的训练场，用于在更换头部、核心、手臂、腿部、FCS、推进器和武器后快速测试锁定速度、姿态恢复、弹道离散、EN 负载和目标击破时间；多作者/机构用于测试 “et al.”。 | `version`, `url`, `organization` |
| `standard` | *Dyson Sphere Program* | CentreBrain; Icarus | English | 《跨恒星系太阳帆群节点寻址、射线接收站安全裕度与戴森壳装配接口标准》：星际制造标准，适合写编号、发布机构和版本。 | `number`, `organization`, `year` |
| `techreport` | 《流浪地球》 | 地球联合政府行星发动机工程验证组; 刘培强 | 中文 | 《重核聚变等离子体约束尺度放大、喷流相干保持与行星发动机阵列工程化验证报告》：工程技术报告，重点写燃料约束、点火稳定性、喷流一致性、阵列同步和从样机到全球工程部署的验证边界。 | `institution`, `type`, `number`, `address` |
| `unpublished` | *Bocchi the Rock!* | Hitori Gotoh; Nijika Ijichi | English | 《小孤独舞台应急便签：想消失前请先看虹夏、数四拍并把音量保持在 6 以下》：未公开排练室便签，不写成论文，而像虹夏为了把波奇从“现场蒸发”边缘拉回来临时整理的演出维持方案。 | `note`, `year` |

## 备选条目池

这些条目可以在正式写 `reference.bib` 时替换或补充上表，避免某些作品过密。

| 作品 | 可替代类型 | 更深入的条目方向 |
| --- | --- | --- |
| *Death Stranding* | `standard`, `manual` | 手性网络带宽元数据、尸体处理合规流程、BB 舱同步误差，以及派送员外骨骼的雨蚀维护周期。 |
| 《三体》 | `techreport`, `standard` | 面壁计划信息隔离规范、智子干扰下的实验重复性准则，或古筝计划前的纳米丝张力标定报告。 |
| *League of Legends* | `dataset`, `article` | 把版本更新说明写成动态系统参数扰动，把英雄平衡写成多目标优化，把投降投票写成群体控制失稳问题。 |
| *The Lord of the Rings* | `map`, `book` | 中土道路网络可靠性、烽火台视距约束、魔多补给线，以及王权复归叙事中的地理信息选择性标注。 |
| 《诡秘之主》 | `archive`, `manual` | 值夜者封印物使用规程、低序列非凡者失控应急流程，或廷根事件后的内部审查和污染溯源档案。 |
| *Frieren* | `book`, `unpublished` | 长寿种族对短寿命样本的低频观测误差、民用魔法目录维护，以及勇者纪念碑长期风化监测。 |
| 《玉子市场》 | `booklet`, `newspaper` | 年糕蒸制湿度控制、商店街节庆客流预测、家族店铺供应链稳定性，以及吉祥物目击事件对销量的统计偏差。 |

## 语言比例建议

正式写入 `reference.bib` 时，可以控制在约 28 条左右：

- 英文条目：约 21 条。
- 中文条目：约 7 条。
- 中文条目优先用于最适合中文语境的作品，如《三体》《流浪地球》《诡秘之主》《黑神话：悟空》《轻音少女》《迷宫饭》《败犬女主太多了！》。
- 英文条目优先用于游戏、奇幻、科幻和国际化设定，如 *Cyberpunk 2077*、*Death Stranding*、*Elden Ring*、*Dark Souls*、*Armored Core VI*、*League of Legends*、*The Lord of the Rings*。

## 下一步

下一步可以把上表改写成真实的 BibTeX 条目。建议先固定每个条目的 citekey 命名规则，例如：

- 英文条目：`nightcity2024cyberpsychosis`、`leyndell2077grace`。
- 中文条目：使用拼音或英文意译，例如 `earthgov2058engineReport`、`tingen1349sequenceStability`。
- 同一作品的条目保留统一前缀，便于在 `temp.tex` 中批量引用和测试排序效果。
