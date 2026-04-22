---
name: robotics-book-translator
description: >
  专为机器人领域书籍翻译而设计的专业技能。当用户需要翻译机器人、自动化、控制系统、运动规划、SLAM、计算机视觉、ROS等机器人学相关书籍、教材或技术文档时，必须使用此技能。核心能力：保持LaTeX/数学公式完整可读、保留图表标题与编号、维持章节层级结构、翻译专业术语时附原文对照。已完成 John J. Craig 《Introduction to Robotics: Mechanics and Control》全书（1-13章 + 附录 A/B/C）翻译验证。触发场景：用户说"翻译这本机器人书"、"把这章翻译成中文"、"翻译robotics教材"、"这段英文是机器人学的，帮我翻译"，或上传包含公式和图表的机器人学PDF/DOCX时，必须触发此技能。即使用户只是说"帮我看看这段robotics内容"也应触发。
---

# 机器人领域书籍翻译技能

## 技能概述

本技能专门处理机器人学、自动化控制、运动规划、机器视觉等领域的技术书籍翻译，核心目标：

1. **格式完整保留** — 章节结构、标题层级、表格、代码块原样还原
2. **公式清晰完整** — LaTeX 公式不丢失、不变形，行内/块级格式正确
3. **插图标注完好** — 图题、图号、图注、坐标轴标签均翻译并保留编号
4. **术语精准一致** — 机器人学专业术语首次出现附英文原词

**实战验证**：已完整翻译 John J. Craig 《Introduction to Robotics: Mechanics and Control》（第 3 版）全书共 13 章 + 三个附录，格式和术语一致性经过实战检验。

---

## 工作流程

### 第一步：分析输入文档

读取文档后，识别以下元素：

```
□ 文档类型（PDF / DOCX / 纯文本 / Markdown 原文提取）
□ 章节结构（H1/H2/H3 层级）
□ 数学公式（行内 $...$ 或块级 $$...$$ / \begin{equation}）
□ 图表（Figure/Table，含编号和标题）
□ 代码块（Python/C++/MATLAB/ROS）
□ 参考文献、脚注
□ 算法伪代码（Algorithm 环境）
□ 附录（三角恒等式、旋转矩阵约定、逆运动学公式）
```

如果是 PDF，先按 `/mnt/skills/public/pdf-reading/SKILL.md` 提取内容；
如果是 DOCX，先按 `/mnt/skills/public/docx/SKILL.md` 提取内容。

### 第二步：术语预处理

翻译前建立术语表（见 `references/robotics-glossary.md`），对文档中出现的专业词汇做统一映射，**避免同词多译**。

### 第三步：逐段翻译（遵循格式规则）

按照下面的 **格式规则** 和 **术语规则** 逐段翻译。原文保留在**原文块**，翻译放在**译文块**，格式为：

```markdown
**原文：**
> 原文内容在这里...

**翻译：**
> 译文内容在这里...
```

### 第四步：输出验证

翻译完成后自检：
- 公式数量是否与原文一致
- 图表编号是否完整
- 术语是否一致（同一术语不出现两种译法）

---

## 格式规则

### 1. 标题层级

保持原文层级，使用 Markdown 标题：

```markdown
# 第3章 运动学（Chapter 3: Kinematics）
## 3.1 正向运动学（Forward Kinematics）
### 3.1.1 D-H 参数法
```

> 规则：章节编号保留原文编号，标题后括号内附英文原标题（仅首次出现该层级时）。

---

### 2. 数学公式

**行内公式** — 保持 `$...$` 格式，不换行：

原文：`The rotation matrix $R \in SO(3)$`  
译文：`旋转矩阵 $R \in SO(3)$`

**块级公式** — 保持 `$$...$$` 或 `\begin{equation}...\end{equation}`，编号保留：

原文：
```
\begin{equation}
  T = \begin{bmatrix} R & p \\ 0 & 1 \end{bmatrix} \in SE(3)
  \label{eq:homogeneous}
\end{equation}
```

译文（公式体不翻译，仅翻译周围文字和标签注释）：
```
齐次变换矩阵定义如下：
\begin{equation}
  T = \begin{bmatrix} R & p \\ 0 & 1 \end{bmatrix} \in SE(3)
  \label{eq:homogeneous}
\end{equation}
其中 $R$ 为旋转矩阵，$p$ 为平移向量。
```

> ⚠️ **公式内符号绝不翻译**，仅翻译公式前后的说明文字和变量定义。
> ⚠️ **Known issue**: `\;` 空格命令在某些 Markdown 渲染环境中会触发内部错误，建议保留原样不修改。

**多行对齐公式**：

```latex
\begin{align}
  \dot{q} &= J^{-1}(q)\, \dot{x} \\
  \tau    &= M(q)\ddot{q} + C(q,\dot{q})\dot{q} + g(q)
\end{align}
```
保持原样，仅翻译紧跟其后的变量说明段落。

**附录旋转矩阵**：整组矩阵保留 LaTeX 原格式，只翻译章节标题和少量说明文字。

---

### 3. 图表处理

**图题格式**：

```
图 3.2：两连杆机械臂的 D-H 坐标系示意图（Figure 3.2: DH frame assignment for 2-link manipulator）
```

**图注/坐标轴标签**：若为矢量图（SVG/TikZ），仅翻译文字标注；若为位图，在图题下方用括号注明坐标轴含义：

```
图 4.1：粒子滤波定位结果
（横轴：时间步 / 纵轴：位置估计误差 [m]）
```

**表格**：表头和内容翻译，表格编号和标题格式如下：

```markdown
**表 5.1：常见机器人运动学参数对比（Table 5.1）**

| 机器人类型 | 自由度 | 工作空间 | 典型应用 |
|-----------|--------|---------|---------|
| 串联机械臂 | 6      | 较大    | 装配     |
```

---

### 4. 代码块

代码**不翻译**，仅翻译代码块上方的说明文字和代码内的注释：

````markdown
以下 ROS 节点实现了基于里程计的位姿估计：

```python
#!/usr/bin/env python
# 订阅里程计话题，发布位姿估计
import rospy
from nav_msgs.msg import Odometry

def odom_callback(msg):
    # 提取位置信息
    x = msg.pose.pose.position.x
```
````

---

### 5. 算法伪代码

```
算法 2.1：扩展卡尔曼滤波（Extended Kalman Filter）

输入：上一时刻状态估计 $\hat{x}_{k-1}$，协方差 $P_{k-1}$，观测 $z_k$
输出：当前时刻状态估计 $\hat{x}_k$，协方差 $P_k$

1: 预测步骤（Prediction）
2:   $\hat{x}_k^- = f(\hat{x}_{k-1}, u_k)$
3:   $P_k^- = F_k P_{k-1} F_k^T + Q_k$
4: 更新步骤（Update）
5:   $K_k = P_k^- H_k^T (H_k P_k^- H_k^T + R_k)^{-1}$
6:   $\hat{x}_k = \hat{x}_k^- + K_k(z_k - h(\hat{x}_k^-))$
7:   $P_k = (I - K_k H_k) P_k^-$
```

> 规则：`Algorithm` → `算法`，关键字（Input/Output/for/while/if）翻译为中文，数学符号保留，步骤编号保留。

---

### 6. 参考文献与脚注

- 参考文献列表**不翻译**，保留原文格式
- 脚注正文翻译，脚注编号保留
- 引用标记 `[1]`、`(Thrun, 2005)` 原样保留

---

## 术语规则

### 核心原则

1. **首次出现** → 中文译名（英文原词）
   - 例：`正向运动学（Forward Kinematics）`
2. **后续出现** → 直接使用中文，无需重复附英文
3. **缩略词** → 首次展开，后续直接用缩略词
   - 例：`同步定位与建图（Simultaneous Localization and Mapping，SLAM）`，后续直接写 `SLAM`

### 标准术语对照表

详细术语表见 `references/robotics-glossary.md`。已实战验证的核心高频术语快速参考：

| 英文 | 中文标准译名 |
|------|-------------|
| Forward Kinematics | 正向运动学 |
| Inverse Kinematics | 逆运动学 |
| Jacobian Matrix | 雅可比矩阵 |
| Degree of Freedom (DOF) | 自由度 |
| End-Effector | 末端执行器 |
| Joint Space | 关节空间 |
| Task/Cartesian Space | 任务空间 / 笛卡尔空间 |
| Configuration Space | 构型空间 |
| Homogeneous Transform | 齐次变换 |
| Denavit-Hartenberg (DH) | D-H 参数法 |
| Workspace | 工作空间 |
| Singularity | 奇异位形 |
| Trajectory Planning | 轨迹规划 |
| Motion Planning | 运动规划 |
| Path Planning | 路径规划 |
| Rapidly-exploring Random Tree (RRT) | 快速扩展随机树 |
| Probabilistic Roadmap (PRM) | 概率路线图法 |
| Potential Field | 势场法 |
| PID Controller | PID 控制器 |
| State Space | 状态空间 |
| Transfer Function | 传递函数 |
| Extended Kalman Filter (EKF) | 扩展卡尔曼滤波 |
| Particle Filter | 粒子滤波 |
| SLAM | 同步定位与建图 |
| Occupancy Grid | 占据栅格 |
| Point Cloud | 点云 |
| Odometry | 里程计 |
| Localization | 定位 |
| Mapping | 建图 |
| Loop Closure | 回环检测 |
| Feature Extraction | 特征提取 |
| Object Detection | 目标检测 |
| Stereo Vision | 立体视觉 |
| Depth Sensor | 深度传感器 |
| LiDAR | 激光雷达 |
| IMU (Inertial Measurement Unit) | 惯性测量单元（IMU）|
| ROS (Robot Operating System) | 机器人操作系统（ROS）|
| Node | 节点（ROS 语境） |
| Topic | 话题 |
| Service | 服务 |
| Action | 动作 |
| Workspace Singularity | 工作空间奇异点 |
| Torque | 力矩 |
| Wrench | 力旋量 |
| Twist | 速度旋量 |
| Screw Theory | 旋量理论 |
| Lie Group / Lie Algebra | 李群 / 李代数 |
| Off-line Programming (OLP) | 离线编程 |
| Task-level Programming (TLP) | 任务级编程 |
| Manipulator | 机械臂 / 操作臂 |
| Calibration | 标定 / 校准 |
| Compliant | 柔顺 |
| Stiffness | 刚度 |

---

## 翻译质量检查清单

翻译完成后，逐项确认：

```
□ 标题编号与原文一致（3.2 → 3.2，不丢失）
□ 所有 $...$ 行内公式完整，无截断
□ 所有 $$...$$ 块级公式完整，编号正确
□ 图题格式：图 X.X：中文描述（英文原题）
□ 表格表头已翻译，表格编号已保留
□ 代码块语言标记保留（```python、```cpp）
□ 算法步骤编号连续
□ 首次出现的术语已附英文原词
□ 同一术语译名全文一致
□ 参考文献未被翻译
□ 公式符号未被错误替换为中文
□ 附录中的矩阵公式完整保留 LaTeX 格式
```

---

## 输出格式

默认输出为 **Markdown**（方便后续转 DOCX/PDF），按章节拆分到 `chapters/` 目录。

如果用户明确要求输出 Word 文档，参考 `/mnt/skills/public/docx/SKILL.md` 生成 `.docx` 文件。

如果用户明确要求输出 PDF，参考 `/mnt/skills/public/pdf/SKILL.md`。

---

## 示例翻译片段

### 输入（英文原文）

> **3.2 The Denavit-Hartenberg Convention**
>
> The D-H convention assigns a coordinate frame to each link of a manipulator. Given $n$ joints, we define $n+1$ frames $\{F_0, F_1, \ldots, F_n\}$. The homogeneous transformation between consecutive frames is:
>
> $$
> ^{i-1}T_i = \begin{bmatrix}
> \cos\theta_i & -\sin\theta_i\cos\alpha_i &  \sin\theta_i\sin\alpha_i & a_i\cos\theta_i \\
> \sin\theta_i &  \cos\theta_i\cos\alpha_i & -\cos\theta_i\sin\alpha_i & a_i\sin\theta_i \\
> 0            &  \sin\alpha_i             &  \cos\alpha_i             & d_i            \\
> 0            &  0                        &  0                        & 1
> \end{bmatrix}
> $$
>
> where $\theta_i$ is the joint angle, $d_i$ the link offset, $a_i$ the link length, and $\alpha_i$ the twist angle. See Figure 3.4 for the frame assignment illustration.

### 输出（中文译文）

> **3.2 D-H 参数法（Denavit-Hartenberg Convention）**
>
> D-H 参数法为机械臂的每个连杆分配一个坐标系。对于具有 $n$ 个关节的机械臂，定义 $n+1$ 个坐标系 $\{F_0, F_1, \ldots, F_n\}$。相邻坐标系之间的齐次变换矩阵（Homogeneous Transformation）为：
>
> $$
> ^{i-1}T_i = \begin{bmatrix}
> \cos\theta_i & -\sin\theta_i\cos\alpha_i &  \sin\theta_i\sin\alpha_i & a_i\cos\theta_i \\
> \sin\theta_i &  \cos\theta_i\cos\alpha_i & -\cos\theta_i\sin\alpha_i & a_i\sin\theta_i \\
> 0            &  \sin\alpha_i             &  \cos\alpha_i             & d_i            \\
> 0            &  0                        &  0                        & 1
> \end{bmatrix}
> $$
>
> 其中 $\theta_i$ 为关节角，$d_i$ 为连杆偏移量，$a_i$ 为连杆长度，$\alpha_i$ 为扭转角。坐标系分配示意图参见图 3.4。

---

## 附加说明

- **长章节处理**：超过 3000 字的章节，分段输出，每段结尾提示"（续下段）"，防止上下文截断
- **扫描版 PDF**：如文档为扫描件且无可选文本，先用 OCR 提取（参见 `/mnt/skills/public/pdf-reading/SKILL.md`），再翻译
- **混合语言文档**：中英文已混排的文档，仅翻译纯英文部分，中文原文保留
- **符号表/索引**：符号表（Notation）中的符号列保留原文，含义列翻译
- **附录处理**：全书末尾的数学公式附录（三角恒等式、旋转矩阵集合、逆运动学公式）保留完整 LaTeX，仅翻译标题和说明文字
- **习题处理**：习题编号保留，题目文字翻译，分值标记（如 `**[15]**`）保留
- **插图提取**：从 PDF 提取插图推荐使用 PyMuPDF，通过 caption 坐标匹配定位图片，页面渲染方式提取比文字OCR更准确
