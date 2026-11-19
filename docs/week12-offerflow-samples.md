# Week 12 OfferFlow 样例记录

记录日期：2026-11-19  
环境：本地 `http://127.0.0.1:8002`  
样例投递：`application_id=6`  
公司：影石创新科技股份有限公司  
岗位：嵌入式实习生

本记录使用已经保存成功的 5 个技能计划。计划均来自当前联网生成流程，
不是人工编写的示例数据。由于这些要求没有固定 Playbook 且有成功抓取的
网页来源，计划状态均为 `generated_grounded`。

## 样例汇总

| 技能要求 | 目标等级 | 预计学时 | 状态 | 来源数 |
|---|---|---:|---|---:|
| 熟练掌握 C/C++ 语言开发，熟悉面向对象设计方法 | L3 | 10 | generated_grounded | 3 |
| 熟悉多线程编程、软件设计模式和算法与数据结构 | L3 | 10 | generated_grounded | 2 |
| 具备阅读英文文档能力 | L3 | 10 | generated_grounded | 2 |
| 熟悉音视频编解码、流媒体协议方向 | L3 | 8 | generated_grounded | 3 |
| 相机软件开发，包括相机应用业务和 UI 实现 | L3 | 10 | generated_grounded | 1 |

合计：5 个计划项，11 个来源。

## 1. C/C++ 与面向对象

搜索主题：

```text
C语言嵌入式编程
C++面向对象设计
面向对象设计方法
```

来源：

- https://www.cnblogs.com/sewain/p/14164181.html
- https://blog.csdn.net/weixin_28895791/article/details/159619961
- https://www.icourse163.org/learn/PKU-1002029030

观察：

- 计划包含类、对象、封装、继承、多态和最小 C++ 练习。
- 一个 GitHub 来源在抓取时超时，但其他来源成功，计划没有中断。

## 2. 多线程、设计模式与数据结构

搜索主题：

```text
FreeRTOS多任务编程
软件设计模式
常用算法与数据结构
```

来源：

- https://www.bilibili.com/video/BV1Jw411i7Fz
- https://www.atguigu.com/video/317

观察：

- 计划结合岗位中的 FreeRTOS 场景，不只给出通用算法课程。

## 3. 英文文档阅读

搜索主题：

```text
英文技术文档阅读
嵌入式英文文档阅读
```

来源：

- https://blog.csdn.net/qq_28576837/article/details/127163667
- https://siphon.ink/docs/english/reading-materials.html

观察：

- 一个网页返回 HTTP 错误，但其他来源仍然支持计划生成。

## 4. 音视频编解码与流媒体

搜索主题：

```text
音视频编解码
流媒体协议
```

来源：

- https://august295.github.io/posts/%E9%9F%B3%E8%A7%86%E9%A2%91%E5%8D%8F%E8%AE%AE%E7%AF%87
- https://developer.volcengine.com/articles/7065630160480911396
- https://github.com/0voice/audio_video_streaming

观察：

- 计划覆盖 RTP/RTCP/RTSP、RTMP、HLS、HTTP-FLV 和实际播放链路分析。

## 5. 相机软件开发

搜索主题：

```text
相机应用开发
相机UI实现
```

来源：

- https://juejin.cn/post/6870357283899342862

观察：

- Android 官方文档抓取超时，但另一个来源成功。
- 计划被分类为 `experience` 后，从“代码练习”调整为
  “小型相机应用实践和过程记录”。

## 分类与排除样例

该投递还包含：

```text
28届毕业同学优先
```

该要求被分类为：

```text
non_learning_constraint
```

它进入 `planning_exclusions`，没有生成课程。

求职者的其他岗位样例中：

```text
热爱电商行业
团队合作与沟通
积极心态与抗压
```

被分类为 `motivation_attitude` 或 `soft_skill`，状态为
`not_applicable`，不参与简历匹配，也不生成学习计划。

## 失败与修复记录

1. 早期多条计划出现：

```text
AttributeError: 'str' object has no attribute 'get'
```

原因是模型有时返回字符串形式的 citation，有时返回对象形式。
服务端现在兼容两种格式。

2. 部分来源出现：

```text
timeout
http_error
```

单个来源失败不会中断整份计划，其他成功来源仍可保存。

3. 最初的通用兜底错误地使用“最小可运行代码练习”描述办公工具。
现在已改为按分类生成通用骨架，不再写死具体软件。

## 当前边界

- 该记录验证了技能计划、真实来源和分类排除。
- 来源标题、URL、抓取时间和正文快照已经保存在
  `LearningPlanItem.sources`。
- 外部网页以后可能改版或下线，引用指纹仍保留在数据库中。
- 当前环境无法代表其他电脑的网络状况，最终用户试用仍需真实走查。
