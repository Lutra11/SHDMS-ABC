# shdms-abc — 自研核心套件（分层结构）

```
algorithm/shdms-abc/
├── modeling/                      # 建模层：列车发车间隔-停站时间联合优化模型
│   └── joint_headway_dwell_model.py   # 论文 §3.1.1–3.1.4（需求/时刻表/容量/目标）
└── optimizer/                     # 算法层：SHDMS-ABC 优化器
    └── shdms_abc.py                   # 论文 §3.2（成功历史驱动动态多策略 ABC）
```

## 两层关系

- **modeling/** 定义优化问题本身：决策变量（区间间隔+停站系数）、客流需求模型、
  容量约束、目标函数与方案评价指标（`ImprovedModel.evaluate_vector`）。
  数据契约指向仓库根的 `datasets/` 目录（NST-HSR 主数据 + 4 条补充线路）。
- **optimizer/** 只负责"怎么搜"：以 `SHDMSABCConfig` 配置驱动四算子
  （差分/精英引导/邻域协作/跳跃变异）的动态概率调度，消费 modeling 给出的
  objective 与 bounds，输出 `SHDMSABCResult`。

## 导入方式

目录名含连字符，不能作为 Python 包名 import。统一入口是顶层
`algorithm` 包：`from algorithm import SHDMSArtificialBeeColony, SHDMSABCConfig`；
实验层继续用 `common.model` / `common.runtime` 门面，完全无感。
内部桥接模块别名为 `shdms_abc_suite`（见 `algorithm/__init__.py`）。
