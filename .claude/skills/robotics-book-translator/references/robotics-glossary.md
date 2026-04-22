# 机器人学专业术语对照表
# Robotics Domain Glossary

本文件为 `robotics-book-translator` 技能的参考术语库，按主题分类。翻译时以本表为准，确保全文术语一致。

---

## 1. 运动学与动力学（Kinematics & Dynamics）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| Forward Kinematics (FK) | 正向运动学 | 由关节角求末端位姿 |
| Inverse Kinematics (IK) | 逆运动学 | 由末端位姿求关节角 |
| Jacobian Matrix | 雅可比矩阵 | 速度映射矩阵 |
| Jacobian Pseudoinverse | 雅可比伪逆 | |
| Denavit-Hartenberg (DH) Parameters | D-H 参数 | |
| Homogeneous Transformation | 齐次变换 | |
| Rotation Matrix | 旋转矩阵 | |
| Translation Vector | 平移向量 | |
| Euler Angles | 欧拉角 | |
| Roll-Pitch-Yaw (RPY) | 横滚-俯仰-偏航角 | 简称 RPY |
| Quaternion | 四元数 | |
| Axis-Angle Representation | 轴角表示 | |
| SO(3) | SO(3) | 三维特殊正交群，不翻译 |
| SE(3) | SE(3) | 三维特殊欧氏群，不翻译 |
| Lie Group | 李群 | |
| Lie Algebra | 李代数 | |
| Screw Theory | 旋量理论 | |
| Twist | 速度旋量 | |
| Wrench | 力旋量 | |
| Degree of Freedom (DOF) | 自由度 | |
| Configuration Space (C-space) | 构型空间 | |
| Joint Space | 关节空间 | |
| Cartesian Space / Task Space | 笛卡尔空间 / 任务空间 | |
| Workspace | 工作空间 | |
| Reachable Workspace | 可达工作空间 | |
| Dexterous Workspace | 灵巧工作空间 | |
| Singularity | 奇异位形 | |
| Redundancy | 冗余度 | |
| Manipulability | 可操作度 | |
| Link | 连杆 | |
| Joint | 关节 | |
| Revolute Joint | 转动关节 | |
| Prismatic Joint | 移动关节 | |
| End-Effector | 末端执行器 | |
| Tool Center Point (TCP) | 工具中心点 | |
| Rigid Body | 刚体 | |
| Generalized Coordinates | 广义坐标 | |
| Inertia Tensor | 惯性张量 | |
| Center of Mass | 质心 | |
| Torque / Moment | 力矩 | |
| Newton-Euler Equations | 牛顿-欧拉方程 | |
| Lagrangian Dynamics | 拉格朗日动力学 | |
| Mass Matrix | 质量矩阵 | 也称惯性矩阵 |
| Coriolis Matrix | 科氏力矩阵 | |
| Gravity Vector | 重力向量 | |
| Equations of Motion | 运动方程 | |

---

## 2. 控制系统（Control Systems）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| PID Controller | PID 控制器 | Proportional-Integral-Derivative |
| Proportional Gain | 比例增益 | |
| Integral Gain | 积分增益 | |
| Derivative Gain | 微分增益 | |
| Feedback Control | 反馈控制 | |
| Feedforward Control | 前馈控制 | |
| Open-Loop Control | 开环控制 | |
| Closed-Loop Control | 闭环控制 | |
| State Space | 状态空间 | |
| State Variable | 状态变量 | |
| Transfer Function | 传递函数 | |
| Bode Plot | 波特图 | |
| Nyquist Criterion | 奈奎斯特判据 | |
| Stability | 稳定性 | |
| Lyapunov Stability | 李雅普诺夫稳定性 | |
| Impedance Control | 阻抗控制 | |
| Force Control | 力控制 | |
| Admittance Control | 导纳控制 | |
| Computed Torque Control | 计算力矩控制 | |
| Model Predictive Control (MPC) | 模型预测控制 | |
| Linear Quadratic Regulator (LQR) | 线性二次调节器 | |
| Adaptive Control | 自适应控制 | |
| Robust Control | 鲁棒控制 | |
| Sliding Mode Control | 滑模控制 | |
| Gain | 增益 | |
| Bandwidth | 带宽 | |
| Steady-State Error | 稳态误差 | |
| Overshoot | 超调量 | |
| Settling Time | 调节时间 | |
| Rise Time | 上升时间 | |
| Eigenvalue | 特征值 | |
| Controllability | 可控性 | |
| Observability | 可观性 | |

---

## 3. 运动规划（Motion Planning）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| Motion Planning | 运动规划 | |
| Path Planning | 路径规划 | |
| Trajectory Planning | 轨迹规划 | |
| Collision Avoidance | 碰撞避免 | |
| Obstacle | 障碍物 | |
| Configuration Space Obstacle (C-obstacle) | 构型空间障碍 | |
| Rapidly-exploring Random Tree (RRT) | 快速扩展随机树 | |
| RRT* | RRT* | 不翻译缩写 |
| Probabilistic Roadmap Method (PRM) | 概率路线图法 | |
| A* Algorithm | A* 算法 | |
| Dijkstra's Algorithm | 迪杰斯特拉算法 | |
| Potential Field Method | 势场法 | |
| Artificial Potential Field | 人工势场 | |
| Sampling-Based Planning | 基于采样的规划 | |
| Grid-Based Planning | 基于栅格的规划 | |
| Roadmap | 路线图 | |
| Visibility Graph | 可见图 | |
| Voronoi Diagram | 维诺图 | |
| Cubic Spline | 三次样条 | |
| Polynomial Trajectory | 多项式轨迹 | |
| Minimum Snap Trajectory | 最小 snap 轨迹 | 无人机控制 |
| Jerk | 加加速度 / 急动度 | |
| Snap | snap | 不翻译 |
| Waypoint | 路径点 | |
| Start Configuration | 初始构型 | |
| Goal Configuration | 目标构型 | |

---

## 4. 定位与地图（Localization & Mapping）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| SLAM (Simultaneous Localization and Mapping) | 同步定位与建图 | 后续直接用 SLAM |
| Localization | 定位 | |
| Mapping | 建图 | |
| Odometry | 里程计 | |
| Dead Reckoning | 航位推算 | |
| Loop Closure | 回环检测 | |
| Place Recognition | 场所识别 | |
| Occupancy Grid Map | 占据栅格地图 | |
| Point Cloud Map | 点云地图 | |
| Feature Map | 特征地图 | |
| Topological Map | 拓扑地图 | |
| Metric Map | 度量地图 | |
| Pose Graph | 位姿图 | |
| Factor Graph | 因子图 | |
| Bundle Adjustment | 光束法平差 | |
| Extended Kalman Filter (EKF) | 扩展卡尔曼滤波 | |
| Unscented Kalman Filter (UKF) | 无迹卡尔曼滤波 | |
| Particle Filter | 粒子滤波 | |
| Monte Carlo Localization (MCL) | 蒙特卡洛定位 | |
| Kalman Filter | 卡尔曼滤波 | |
| Covariance Matrix | 协方差矩阵 | |
| Measurement Model | 观测模型 | |
| Motion Model | 运动模型 | |
| Sensor Fusion | 传感器融合 | |
| Maximum Likelihood Estimation (MLE) | 最大似然估计 | |
| Maximum a Posteriori (MAP) | 最大后验估计 | |
| Belief | 置信度/信念分布 | 贝叶斯滤波中的 bel(x) |
| Landmark | 路标点 | |
| Data Association | 数据关联 | |

---

## 5. 传感器与感知（Sensors & Perception）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| LiDAR (Light Detection and Ranging) | 激光雷达 | 后续直接用 LiDAR |
| RGB-D Camera | RGB-D 相机 | |
| Stereo Camera | 双目相机 | |
| Monocular Camera | 单目相机 | |
| IMU (Inertial Measurement Unit) | 惯性测量单元 | |
| Accelerometer | 加速度计 | |
| Gyroscope | 陀螺仪 | |
| Encoder | 编码器 | |
| Depth Sensor | 深度传感器 | |
| Sonar | 声呐 | |
| GPS/GNSS | GPS/GNSS | 不翻译 |
| Point Cloud | 点云 | |
| Voxel | 体素 | |
| Normal Vector | 法向量 | |
| Feature Extraction | 特征提取 | |
| Feature Descriptor | 特征描述子 | |
| SIFT | SIFT | 尺度不变特征变换，后续直接用 SIFT |
| ORB | ORB | 不翻译 |
| FAST Keypoint | FAST 角点 | |
| Optical Flow | 光流 | |
| Epipolar Geometry | 对极几何 | |
| Essential Matrix | 本质矩阵 | |
| Fundamental Matrix | 基础矩阵 | |
| Homography | 单应矩阵 | |
| Camera Calibration | 相机标定 | |
| Intrinsic Parameters | 内参 | |
| Extrinsic Parameters | 外参 | |
| Distortion Coefficients | 畸变系数 | |
| Projection Matrix | 投影矩阵 | |
| Disparity Map | 视差图 | |
| Object Detection | 目标检测 | |
| Semantic Segmentation | 语义分割 | |
| Instance Segmentation | 实例分割 | |
| Bounding Box | 边界框 | |

---

## 6. 机器学习与强化学习（ML & RL in Robotics）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| Reinforcement Learning (RL) | 强化学习 | |
| Policy | 策略 | |
| Reward Function | 奖励函数 | |
| State | 状态 | |
| Action | 动作 | 注意区分 ROS action |
| Observation | 观测 | |
| Episode | 回合 | |
| Markov Decision Process (MDP) | 马尔可夫决策过程 | |
| Q-Learning | Q 学习 | |
| Deep Q-Network (DQN) | 深度 Q 网络 | |
| Policy Gradient | 策略梯度 | |
| Actor-Critic | 演员-评论家 | |
| Proximal Policy Optimization (PPO) | 近端策略优化 | |
| Sim-to-Real Transfer | 仿真到实物迁移 | |
| Domain Randomization | 域随机化 | |
| Imitation Learning | 模仿学习 | |
| Inverse Kinematics Neural Network | 神经网络逆运动学 | |
| Convolutional Neural Network (CNN) | 卷积神经网络 | |
| Recurrent Neural Network (RNN) | 循环神经网络 | |

---

## 7. ROS 与软件框架（ROS & Software）

| 英文术语 | 中文标准译名 | 说明/备注 |
|---------|------------|---------|
| ROS (Robot Operating System) | 机器人操作系统（ROS）| 首次展开，后续直接用 ROS |
| ROS 2 | ROS 2 | 不翻译 |
| Node | 节点 | ROS 语境 |
| Topic | 话题 | ROS 语境 |
| Message | 消息 | ROS 语境 |
| Service | 服务 | ROS 语境 |
| Action | 动作 | ROS 语境 |
| Launch File | 启动文件 | |
| Parameter Server | 参数服务器 | |
| TF (Transform) | TF 坐标变换 | |
| URDF | URDF | 统一机器人描述格式 |
| Gazebo | Gazebo | 仿真器，不翻译 |
| MoveIt | MoveIt | 运动规划框架，不翻译 |
| Nav2 | Nav2 | 导航框架，不翻译 |
| PCL (Point Cloud Library) | 点云库（PCL）| |
| OpenCV | OpenCV | 不翻译 |
| Eigen | Eigen | 矩阵库，不翻译 |
| Publisher | 发布者 | |
| Subscriber | 订阅者 | |
| Callback | 回调函数 | |

---

## 8. 机器人类型（Robot Types）

| 英文术语 | 中文标准译名 |
|---------|------------|
| Serial Manipulator | 串联机械臂 |
| Parallel Manipulator | 并联机械臂 |
| Mobile Robot | 移动机器人 |
| Wheeled Robot | 轮式机器人 |
| Legged Robot | 足式机器人 |
| Quadruped | 四足机器人 |
| Humanoid Robot | 仿人机器人 |
| UAV / Drone | 无人机 |
| Unmanned Ground Vehicle (UGV) | 无人地面车辆 |
| Collaborative Robot (Cobot) | 协作机器人 |
| Differential Drive | 差速驱动 |
| Holonomic | 完整约束 |
| Non-holonomic | 非完整约束 |
| Omni-directional | 全向 |
| Mecanum Wheel | 麦克纳姆轮 |

---

## 使用说明

1. 本表仅收录高频核心术语，翻译中遇到未收录术语，参考如下原则：
   - 优先查阅《机器人学》（Craig）、《概率机器人学》（Thrun）中文版的译法
   - 其次参考 IEEE Robotics and Automation Society 官方中文资料
   - 新造词以"意译为主，音译为辅"原则处理

2. 专有名词（人名、地名、算法名）一般不翻译：
   - ✅ `Denavit-Hartenberg` → D-H 参数法（保留原名缩写）
   - ✅ `Gazebo`、`ROS`、`MoveIt` → 直接用，首次附括号解释

3. 单位不翻译：`rad`、`m/s`、`N·m`、`Hz` 等保留原文
