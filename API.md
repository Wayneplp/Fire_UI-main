# API.md — PyWebView 后端接口文档（供前端对接）

> 适用范围：本项目采用 **pywebview** 将 Python 后端对象暴露为 `window.pywebview.api`，前端通过 `await window.pywebview.api.xxx()` 调用后端方法获取数据或下发控制指令。  
> 说明：本文档依据当前仓库内 `can_init.py / data_storage.py / index.js` 的实现整理。

---

## 1. 调用约定

- **调用入口**：`window.pywebview.api`
- **调用方式**：所有接口均为异步 Promise（前端需 `await`）
- **返回类型**：Python 的 `dict / list` 会被自动序列化为 JS Object / Array
- **错误处理**：多数接口以 `{"status": "success"}` / `{"status":"error","message":"..."}` 表示结果；个别接口存在成功状态字符串不一致，见“附录 A：对接风险点”。

示例：

```js
const api = window.pywebview.api;

// 搜索 PCAN
const info = await api.search_serial_ports();

// 连接
const res = await api.connect_serial_port(selectedPort);

// 拉取主机列表
const data = await api.get_all_hosts();
```

---

## 2. 连接与设备相关接口

### 2.1 搜索设备（PCAN）

**方法名**：`search_serial_ports()`

**参数**：无

**返回**：

- 成功（检测到 PCAN）：

```json
{
  "Device_name": "PEAK-System PCAN USB",
  "Channel": "PCAN_USBBUS1",
  "Interface": "pcan"
}
```

- 未检测到设备：返回空对象 `{}`

**前端用途**：用于下拉框展示可用设备信息（通常以 `Device_name` 作为显示字段）。

---

### 2.2 连接 PCAN

**方法名**：`connect_serial_port(port_name=None)`

**参数**：
- `port_name`：string，可选（当前实现为兼容前端传参，CAN 情况下通常不会真正依赖该值）

**返回**：

- 成功：

```json
{
  "status": "Connected",
  "pcan_info": {
    "Device_name": "PEAK-System PCAN USB",
    "Channel": "PCAN_USBBUS1",
    "Interface": "pcan"
  }
}
```

- 失败：

```json
{
  "status": "Error",
  "pcan_info": {}
}
```

---

### 2.3 断开连接

**方法名**：`disconnect_serial_port()`

**参数**：无

**返回**：

```json
{
  "status": "Disconnected",
  "is_connected": false,
  "current_port": null
}
```

---

### 2.4 获取连接状态

**方法名**：`get_connection_status()`

**参数**：无

**返回**：

```json
{
  "is_connected": true,
  "pcan_info": {
    "Device_name": "PEAK-System PCAN USB",
    "Channel": "PCAN_USBBUS1",
    "Interface": "pcan"
  }
}
```

---

## 3. 主机列表页接口

### 3.1 获取所有主机列表 + 异常主机问题列表

**方法名**：`get_all_hosts()`

**参数**：无

**返回**：

```json
{
  "hostStatus": [
    {
      "hostname": "主机1",
      "zhujiid": 1,
      "sensorCount": 12,
      "faultCount": 1,
      "alertCount": 2,
      "alertLevel": 3,
      "inputs": [false, true, false, false, false, false, false, false],
      "outputs": [true, false, false, false, false, false, false, false],
      "outputs_lock": [true, true, true, true, true, true, true, true],
      "status": "火警"
    }
  ],
  "hostProblems": [
    {
      "hostname": "主机1",
      "zhujiid": 1,
      "sensorCount": 12,
      "faultCount": 1,
      "alertCount": 2,
      "alertLevel": 3,
      "inputs": [...],
      "outputs": [...],
      "outputs_lock": [...],
      "status": "火警",
      "problem": "最高警报级别3；出现2个警报；出现1个故障",
      "severity": "alert"
    }
  ]
}
```

**字段说明（hostStatus 单条）**：

| 字段 | 类型 | 说明 |
|---|---:|---|
| hostname | string | 显示用名称，如“主机12” |
| zhujiid | number | 主机 ID（1~200） |
| sensorCount | number | 在线探测器数量（主板上报） |
| faultCount | number | 故障数量（主板上报） |
| alertCount | number | 警报数量（主板上报） |
| alertLevel | number | 最高警报等级（主板上报） |
| inputs | boolean[8] | 8 路输入状态 |
| outputs | boolean[8] | 8 路输出状态 |
| outputs_lock | boolean[8] | 8 路输出锁/模式（常用于自动/手动判断） |
| status | string | `正常/异常/火警/离线/未知`（由后端推导） |

**字段说明（hostProblems 单条）**：
- 在 hostStatus 基础上，补充：
  - `problem`：组合文字描述
  - `severity`：`alert`（存在警报）或 `fault`（仅故障）

---

## 4. 主机详情页接口

### 4.1 获取指定主机详情

**方法名**：`get_host_data(hid)`

**参数**：
- `hid`：number，主机 ID（如 1）

**返回**：

```json
{
  "selectedHostInfo": {
    "onlineSensors": 12,
    "problemCount": 3,
    "alertLevel": 2
  },
  "detectors": [
    {
      "hostname": "主机1",
      "zhujiid": 1,
      "detectorId": "1",
      "signalStrength": 8,
      "faultStatus": 0,
      "alarmLevel": 0,
      "coAlarmLevel": 0,
      "smokeAlarmLevel": 0,
      "tempAlarmLevel": 0,
      "vocAlarmLevel": 0,
      "hydrogenAlarmLevel": 0,
      "sensorEnable": 1,
      "vocEnable": 1,
      "temperature": "25℃",
      "co": "1.2ppm",
      "smoke": "0.010dbm",
      "voc": "10ppm",
      "hydrogen": "0ppm",
      "tempRiseAlarm": 0,
      "tempExceedAlarm": 0,
      "smokeDetected": 0,
      "smokeExceedAlarm": 0,
      "coRiseAlarm": 0,
      "coExceedAlarm": 0,
      "h2RiseAlarm": 0,
      "h2ExceedAlarm": 0,
      "vocRiseAlarm": 0,
      "vocExceedAlarm": 0,
      "name": "探测器1",
      "signal": "80%"
    }
  ],
  "subboards": [
    {
      "hostname": "主机1",
      "zhujiid": 1,
      "subboardId": "1",
      "signalStrength": 8,
      "outputs": [true, false],
      "inputs": [false, true, false],
      "id": "分区控制器1",
      "signal": "80%"
    }
  ],
  "currentHostFaults": [
    { "name": "探测器1", "description": "温度超标警报" }
  ],
  "outputsStatus": [true, false, ...],
  "outputslockStatus": [true, true, ...],
  "dcControlStatus": [true, false, ...],
  "inputsStatus": [false, true, ...]
}
```

**字段说明（selectedHostInfo）**：
- `onlineSensors`：在线探测器数量（detectors 列表中信号强度 > 0 的数量）
- `problemCount`：当前主机故障/告警项总数（由后端汇总）
- `alertLevel`：主机最高警报等级

**字段说明（detectors）**：
- `detectorId`：探测器编号（字符串）
- `signalStrength`：信号强度（0~?）
- `faultStatus / alarmLevel / ...`：探测器故障与各类告警等级
- `temperature / co / smoke / voc / hydrogen`：后端格式化后的展示字符串（带单位）
- `tempRiseAlarm / tempExceedAlarm / ...`：按位或按字段拆出的细分告警标志位
- `name`：前端展示名（如“探测器1”）
- `signal`：信号百分比字符串（如“80%”）

**字段说明（subboards）**：
- `subboardId`：子板编号
- `outputs`：2 路输出
- `inputs`：3 路输入
- `id`：展示名（如“分区控制器1”）

---

## 5. 控制相关接口

### 5.1 控制主机输出/模式

**方法名**：`control_dc(hostid, switch_number, status)`

**参数**：
- `hostid`：number，主机 ID
- `switch_number`：number  
  - `1~8`：对应 8 路输出（后端会转为 0~7 写入 CAN data[3]）
  - `9`：自动/手动模式切换（后端发送另一种 CAN 数据格式）
- `status`：boolean，目标状态  
  - `true`：开 / 自动  
  - `false`：关 / 手动

**返回（期望）**：

- 成功：
```json
{ "status": "success" }
```

- 失败：
```json
{ "status": "error", "message": "..." }
```

---

## 6. 笔记相关接口（如页面使用）

### 6.1 保存笔记

**方法名**：`save_notes(title, content)`

**参数**：
- `title`：string
- `content`：string

**返回**：
- 成功：`{"status":"success"}`
- 失败：`{"status":"error","message":"..."}`

---

### 6.2 获取笔记

**方法名**：`get_notes()`

**参数**：无

**返回**：

```json
{ "title": "...", "content": "..." }
```

---

## 7. 调试/数据流接口（可选）

### 7.1 获取最新一帧解析后的 CAN 数据（出队）

**方法名**：`get_latest_frame()`

**参数**：无

**返回**：

- 队列有数据：
```json
{
  "has_frame": true,
  "frame": {
    "frame_type": 1,
    "main_board_id": 5,
    "sub_board_id": 1,
    "data": [0,1,2,3,4,5,6,7]
  }
}
```

- 队列为空：
```json
{ "has_frame": false, "frame": null }
```

---

## 8. CAN 帧解析约定（便于前端理解数据来源）

后端对 CAN 扩展 ID 做固定拆解，示意如下（仅用于理解）：

- `cmd` = (id >> 24) & 0xFF  → 映射为 `frame_type`
- `board_id` = (id >> 16) & 0xFF → `main_board_id`
- `fixed` = (id >> 8) & 0xFF → 必须等于 `0xF5`，否则丢弃
- `ex_id` = id & 0xFF → `sub_board_id`
- 仅接收 `dlc==8` 且非 error/remote 帧

`frame_type` 与数据模型对应关系：
- `0x01`：主板状态（在线/故障/警报/IO/锁等）
- `0x02`：子板状态（信号强度 + 2 输出 + 3 输入）
- `0x03`：探测器状态（信号/故障/各类告警等级）
- `0x04`：探测器数值（温度/CO/烟雾/H2/VOC 等原始值）
- `0x05`：探测器告警（上升/超标等；H2/VOC 采用高4位/低4位拆分）
- `0x10`：历史数据结构已预留，但当前 `update_data()` 未实现（不会进入 DataStorage）

---

## 附录 A：对接风险点（建议尽快统一）

1. **control_dc 成功判定不一致**  
   - `send_control_command()` 成功返回 `"status": "Connected"`  
   - `control_dc()` 中却按 `"status" == "OK"` 判定成功  
   - 结果：后端可能误判为失败，前端收到 `{"status":"error"}`  
   **建议**：统一成功状态为 `"OK"` 或在 `control_dc()` 中兼容 `"Connected"`。

2. **connect_can 失败原因未透传**  
   - 连接失败时内部会产生 `error` 字段，但返回体未包含  
   **建议**：返回 `{"status":"Error","message":"...","pcan_info":{}}` 便于前端提示。

---

## 附录 B：前端建议的接口封装（可选）

建议前端统一封装一层：

```js
const api = window.pywebview.api;

export async function Api_SearchPcan() {
  return await api.search_serial_ports();
}

export async function Api_Connect() {
  return await api.connect_serial_port();
}

export async function Api_GetAllHosts() {
  return await api.get_all_hosts();
}

export async function Api_GetHostData(id) {
  return await api.get_host_data(id);
}

export async function Api_Control(hostid, sw, status) {
  return await api.control_dc(hostid, sw, status);
}
```

这样页面逻辑更清晰，也方便以后替换为 HTTP/WebSocket。
