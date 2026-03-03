# 110kV 电网仿真工程（pandapower + FastAPI）

## 功能
- 电网构建：从外部接口载入 JSON，自动补全缺失关键元素。
- 故障模拟与恢复：支持线路/变压器/三绕组变/开关/机组/负荷故障下线与恢复。
- 电网状态获取：执行潮流并返回母线电压、线路负载率。
- N-1 安全扫描：对线路和双绕组变逐一断开并检查越限/不收敛。
- 模型状态管理：快照保存与恢复。
- 实时数据接入：在线更新机组与负荷功率。
- 负荷转供与恢复：按比例将负荷迁移到目标母线。
- 预测能力：提供简化短时预测（可替换为机器学习模型）。

## 启动
```bash
pip install -e .
uvicorn app.main:app --reload --port 8000
```

## 关键接口
- `POST /api/v1/grid/build`
- `GET /api/v1/grid/state`
- `POST /api/v1/grid/fault`
- `POST /api/v1/grid/recover`
- `GET /api/v1/grid/nminus1`
- `POST /api/v1/grid/realtime`
- `POST /api/v1/grid/transfer`
- `POST /api/v1/grid/snapshot`
- `POST /api/v1/grid/restore`
- `GET /api/v1/grid/predict`

## 说明
- 若输入缺少必要结构（如 BUSBAR/ACLINE/TRANSFORMER 等），系统会自动补位。
- 对于未出现的母线 ID，会按默认 110kV 母线参数自动创建，保障可运行性。
