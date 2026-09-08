import json
from dataclasses import dataclass, field
import time  # 添加在文件开头

@dataclass
class MainBoard:
    # 主板数据 (0x01帧)
    detector_online_count: int = 0    # 探测器在线数量
    subboard_online_count: int = 0    # 子板在线数量
    fault_count: int = 0              # 故障数量
    alarm_count: int = 0              # 警报数量
    max_alarm_level: int = 0          # 警报最高级别
    outputs: list = field(default_factory=lambda: [False] * 8)  # 8个输出状态
    inputs: list = field(default_factory=lambda: [False] * 8)   # 8个输入状态
    outputs_lock: list = field(default_factory=lambda: [False] * 8)  # 8个输出状态锁
    last_update_time: float = field(default_factory=time.time)  # 最后更新时间

    def update_from_data(self, frame_type, data):
        """更新主板数据
        Args:
            frame_type: 帧类型
            data: 数据内容
        """
        if frame_type == 0x01:  # 主板数据帧
            self.detector_online_count = data[0]
            self.subboard_online_count = data[1]
            self.fault_count = data[2]
            self.alarm_count = data[3]
            self.max_alarm_level = data[4]
            
            # 将字节转换为8位二进制，并转换为布尔值列表
            output_byte = data[5]
            self.outputs = [bool(output_byte & (1 << i)) for i in range(8)]  # 从低位到高位
            
            # 同样处理输入状态
            input_byte = data[6]
            self.inputs = [bool(input_byte & (1 << i)) for i in range(8)]  # 从低位到高位

            # 处理输出锁状态
            output_lock_byte = data[7]  # 使用第8个字节作为输出锁状态
            self.outputs_lock = [bool(output_lock_byte & (1 << i)) for i in range(8)]  # 从低位到高位
            
            self.last_update_time = time.time()

            # 打印更新后的状态
            '''
            print(f"\n主板数据更新:")
            print(f"探测器在线数量: {self.detector_online_count}")
            print(f"子板在线数量: {self.subboard_online_count}")
            print(f"故障数量: {self.fault_count}")
            print(f"警报数量: {self.alarm_count}")
            print(f"警报最高级别: {self.max_alarm_level}")
            print(f"输出状态: {self.outputs}")
            print(f"输入状态: {self.inputs}")
            print(f"输出状态锁: {self.outputs_lock}")
            print(f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_update_time))}\n")
            '''

@dataclass
class SubBoard:
    # 子版数据 (0x02帧)
    signal_strength: int = 0          # 在线信号强度
    outputs: list = field(default_factory=lambda: [False] * 2)  # 2个输出状态
    inputs: list = field(default_factory=lambda: [False] * 3)   # 3个输入状态

    def update_from_data(self, frame_type, data):
        """更新子板数据
        Args:
            frame_type: 帧类型
            data: 数据内容
        """
        if frame_type == 0x02:  # 子板数据帧
            self.signal_strength = data[0]
            self.outputs = [bool(data[1]), bool(data[2])]  # 2个输出状态
            self.inputs = [bool(data[3]), bool(data[4]), bool(data[5])]  # 3个输入状态

@dataclass
class Detector:
    # 状态数据 (0x03帧)
    signal_strength: int = 0          # 在线信号强度
    fault_status: int = 0             # 故障情况
    alarm_level: int = 0              # 警报级别
    co_alarm_level: int = 0           # 一氧化碳警报级别
    smoke_alarm_level: int = 0        # smoke警报级别
    temp_alarm_level: int = 0         # 温度警报级别
    voc_alarm_level: int = 0          # voc警报级别
    hydrogen_alarm_level: int = 0     # 氢气警报级别

    # 数值数据 (0x04帧)
    sensor_enable: int = 0            # 传感器启用状态
    voc_enable: int = 0              # VOC传感器启用状态
    temperature: int = 0             # 温度值
    co_value: int = 0               # 一氧化碳浓度值
    smoke_value: int = 0            # 烟雾值
    hydrogen_value: int = 0         # 氢气值
    voc_value: int = 0              # VOC值

    # 警报数据 (0x05帧)
    temp_rise_alarm: int = 0          # 温度上升警报
    temp_exceed_alarm: int = 0        # 温度超标警报
    smoke_detected: int = 0           # 烟雾检测
    smoke_exceed_alarm: int = 0       # 烟雾超标警报
    co_rise_alarm: int = 0           # 一氧化碳上升警报
    co_exceed_alarm: int = 0         # 一氧化碳超标警报
    h2_rise_alarm: int = 0           # 氢气上升警报
    h2_exceed_alarm: int = 0         # 氢气超标警报
    voc_rise_alarm: int = 0          # VOC上升警报
    voc_exceed_alarm: int = 0        # VOC超标警报


    def update_from_data(self, frame_type, data):
        if frame_type == 0x03:  # 探测器状态帧
            self.signal_strength = data[0]
            self.fault_status = data[1]
            self.alarm_level = data[2]
            self.co_alarm_level = data[3]
            self.smoke_alarm_level = data[4]
            self.temp_alarm_level = data[5]
            self.voc_alarm_level = data[6]
            self.hydrogen_alarm_level = data[7]

        elif frame_type == 0x04:  # 探测器数值帧
            self.sensor_enable = data[0]
            self.voc_enable = data[1]
            self.temperature = data[2]
            self.co_value = data[3]
            self.smoke_value = data[4]
            self.hydrogen_value = data[5]
            self.voc_value = data[6]

        elif frame_type == 0x05:  # 探测器警报帧
            self.temp_rise_alarm = data[0]
            self.temp_exceed_alarm = data[1]
            self.smoke_detected = data[2]
            self.smoke_exceed_alarm = data[3]
            self.co_rise_alarm = data[4]
            self.co_exceed_alarm = data[5]
            h2_byte = data[6]   
            # 如果底层只是 0/1，这样解就行；以后他们要扩展成 0~15 也兼容
            self.h2_rise_alarm      = (h2_byte >> 4) & 0x0F   # 高 4 位
            self.h2_exceed_alarm    = h2_byte & 0x0F          # 低 4 位
            voc_byte = data[7]
            self.voc_rise_alarm   = (voc_byte >> 4) & 0x0F  # 高 4 位
            self.voc_exceed_alarm  = voc_byte & 0x0F         # 低 4 位  


# —-----------------------------------------------------历史数据处理---------  void store_history_record  -------------------------
@dataclass
class History_data:
    Warning_Type = 1
    Sensor_Type  = 2
    Control_Type = 3
    Fault_Type   = 4
    Trig_Type    = 5
    Out_Type     = 6
    
     # -------- 0x00：严格视为异常（不要误判成 fault）--------
    
    # 保证每个 History_data 实例都有自己独立的空列表
    records: list = field(default_factory=list)  # 存历史记录列表
    Event_Map = {
        () : ("fault_type","0")
    }

    def update_from_data(self, data):
        # data: 8 bytes payload，里面的数值你视为“码值”（0x..）
        param0 = int(data[0])
        param1 = int(data[1])
        event_id = int(data[2])
        event_type = int(data[3])

        level, msg = self._decode_message(event_type, event_id, param0, param1)

        rec = {
            "time": time.time(),
            "type": event_type,
            "id": event_id,
            "param0": param0,
            "param1": param1,
            "level": level,
            "message": msg,
            "raw": list(data),
        }

        # 十六进制方式打印，符合你“全是16进制”的习惯
        print(
            "[HISTORY 0x10] "
            f"type=0x{event_type:02X} id=0x{event_id:02X} "
            f"p0=0x{param0:02X} p1=0x{param1:02X} "
            f"level={level} msg={msg} raw={[f'0x{x:02X}' for x in rec['raw']]}"
        )

        self.records.append(rec)
        if len(self.records) > 2000:
            self.records = self.records[-2000:]

        # print(
        #     "DBG",
        #     "data=", data,
        #     "list=", list(data),
        #     "hex=", [f"0x{x:02X}" for x in data],
        #     "mapped:",
        #     f"type=0x{event_type:02X}",
        #     f"id=0x{event_id:02X}",
        #     f"p0=0x{param0:02X}",
        #     f"p1=0x{param1:02X}",
        #     "types:",
        #     type(data[0]), type(event_id)
        # )
   
    def _decode_message(self, event_type, event_id, param0, param1):
         # -------- 0x00：严格视为异常（不要误判成 fault）--------
        if event_type == 0x00:
            return (
                "unknown",
                f"type=0x00(非法/未定义) id=0x{event_id:02X} p0=0x{param0:02X} p1=0x{param1:02X}"
            )
        # ===================== Warning (1) =====================
        if event_type == self.Warning_Type:
            # 手动报警：id=0x40, p0=0x40, p1=0x40
            if event_id == 0x40 and param0 == 0x40 and param1 == 0x40:
                return ("warning", "手动报警触发")

            # 五合一触发：p0=0x53
            if param0 == 0x53:
                return ("warning", f"五合一触发：编号{event_id}")
            # 主板触发
            if param0 == 0x0B:
                display_id = (event_id - 31) & 0xFF
                return ("warning", f"主机{display_id}号出现火情")
            if param0 ==0x28:
                return ("warning", "手动报警触发")
            # 子板触发：p0=0x33
            if param0 == 0x21:
                board_id = event_id // 3
                input_id = event_id % 3
                return ("warning", f"{board_id}号分区{input_id + 1}号警报")
            # 探测器温度报警：data0==51
            if param0 == 0x33:  # 51
                return ("warning", f"探测器{event_id}温度报警")
            # # 温度报警：p0=0x51
            # if param0 == 0x51:
            #     return ("warning", f"探测器{event_id} 温度报警（等级=0x{param1:02X}）")
            # 探测器烟雾报警：data0==52
            if param0 == 0x34:  # 52
                return ("warning", f"探测器{event_id}烟雾报警")
            # # 烟雾报警：p0=0x52
            # if param0 == 0x52:
            #     return ("warning", f"探测器{event_id} 烟雾报警（等级=0x{param1:02X}）")
            # 探测器报警：data0==53
            if param0 == 0x35:  # 53
                return ("warning", f"探测器{event_id}报警")

            return ("warning", f"探测器{event_id} 预警/报警（code=0x{param0:02X}, level=0x{param1:02X}）")
        # ===================== Sensor (2) =====================
        if event_type == self.Sensor_Type:
            # MCU: data0==1 CO, data0==2 H2, data0==3 VOC
            if param0 == 0x01:
                return ("warning", f"{event_id}号CO报警")
            if param0 == 0x02:
                return ("warning", f"{event_id}号H2报警")
            if param0 == 0x03:
                return ("warning", f"{event_id}号VOC报警")
            return ("warning", f"{event_id}号气体报警（code=0x{param0:02X}）")
        # ===================== Control (3) =====================
        if event_type == self.Control_Type:
            # data0 == 1：自检/消音/复位
            if param0 ==0x01:
                if param1 ==0x01:
                    return ("info", f"用户点击自检")
                if param1 == 0x02:
                    return ("info", f"用户点击消音")
                if param1 ==0x03:
                    return ("info", f"用户点击复位")
                return ("info", f"用户点击未知功能键（p1=0x{param1:02X}）")
            # data0 == 2：手动报警/紧急启动/紧急停止/主机紧急启动/主机紧急停止/模式切换
            if param0 ==0x02:
                if param1 ==0x01:
                    return ("info", f"用户点击手动报警")
                if param1 ==0x02:
                    return ("info", f"用户点击紧急启动")
                if param1 ==0x03:
                    return ("info", "用户点击紧急停止")
                if param1 == 0x04:
                    return ("info", "用户点击主机上紧急启动")
                if param1 == 0x05:
                    return ("info", "用户点击主机上紧急停止")
                if param1 == 0x06:
                     # MCU: if(ID==1) 自动模式; else if(ID==0) 手动模式
                    if event_id == 0x01:
                        return ("info", "自动模式")
                    if event_id == 0x00:
                        return ("info", "手动模式")
                    return ("info", f"模式切换（id=0x{event_id:02X}）")
                return ("info", "用户点击未知按钮操作")
            # data0 == 3：灭火器启动/停止
            if param0 == 0x03:
                if param1 == 0x01:
                    return ("info", "灭火器启动")
                if param1 == 0x00:
                    return ("info", "灭火器停止")
                return ("info", f"灭火器控制（p1=0x{param1:02X}）")
            # data0 == 4：分区输出开关（ID=分区号，data1=输出动作码）
            if param0 == 0x04:
                zone = event_id  # MCU: snprintf(..., record->ID)

                if param1 == 0x0B:  # 11 -> 分区1输出开启
                    return ("info", f"{zone}号分区1号输出开启")
                if param1 == 0x0A:  # 10 -> 分区1输出关闭
                    return ("info", f"{zone}号分区1号输出关闭")
                if param1 == 0x15:  # 21 -> 分区2输出开启
                    return ("info", f"{zone}号分区2号输出开启")
                if param1 == 0x14:  # 20 -> 分区2输出关闭
                    return ("info", f"{zone}号分区2号输出关闭")

                return ("info", f"{zone}号分区输出控制（code=0x{param1:02X}）")
            # 按键长按5秒紧急启动：id=0x00, p0=0x02, p1=0x02/0x04
            if event_id == 0x00 and param0 == 0x02:
                if param1 == 0x02:
                    return ("info", "按键1长按5秒：紧急启动触发")
                if param1 == 0x04:
                    return ("info", "按键3长按5秒：紧急启动触发")
                return ("info", f"紧急启动触发（p1=0x{param1:02X}）")

            # 网页触发：event_id=0x00~0x1F, p1==0x00, p0==0/1
            if 0x00 <= event_id <= 0x1F and param1 == 0x00:
                if param0 == 0x01:
                    return ("info", f"网页触发：{event_id}号触发")
                if param0 == 0x00:
                    return ("info", f"网页触发：{event_id}号触发消失")
                return ("info", f"网页触发：{event_id}号（p0=0x{param0:02X}）")

            return ("info", f"控制事件 id=0x{event_id:02X}（p0=0x{param0:02X}, p1=0x{param1:02X}）")
        
        
        
            # ===================== Fault (4) =====================
        if event_type == self.Fault_Type:
            # 电源故障：id=0x29, p0=0x29, p1=0x29/0x2A
            if event_id == 41 and param0 == 41 :
                if param1 == 41:
                    return ("fault", "主电故障，备电工作")
                if param1 == 42:
                    return ("fault", "备电故障")
                if param1 == 40:
                    return ("fault", "恢复主电工作")     
            # 探测器故障：id=探测器号, p0=0x00, p1=故障码  
            if 1 <= event_id <= 200 and param0 == 0x00: # 探测器故障：id=探测器号, p0=0x00, p1=故障码
                if param1 == 0x01:
                    return ("warning", f"探测器{event_id}号灭火器启动")
                if param1 ==0x02:
                    return ("fault", f"探测器{event_id}号故障")
                if param1==0x03:
                    return ("fault", f"探测器{event_id}号硬件故障")
                if param1==0x04:
                    # return ("fault", f"探测器{event_id}号初始化")
                    return("Null")
                return ("unknown", f"探测器{event_id}号事件未知(type=0x00, code=0x{param1:02X})")
            # 探测器、控制器离线
            if 1 <= event_id <= 200 and param0 == 0x01:
                return ("fault", f"探测器{event_id}号离线")    
            if 1 <= event_id < 200 and param0 == 0x02:
                return ("fault", f"控制器{event_id} 离线")


            # CAN 总线错误：id=0x00, p0=0x02, p1=0x01/0x02
            if param0 == 0x02:
                if param1 == 0x01:
                    return ("fault", "CAN1 总线错误")
                if param1 == 0x02:
                    return ("fault", "CAN2 总线错误")
                return ("fault", f"CAN 总线错误（通道=0x{param1:02X}）")
            # # 探测器离线：p0=0x01, p1=探测器号（你MCU里也写成 i），event_id=探测器号
            # if param0 == 0x01:
            #     # 常见一致性：event_id 和 param1 都等于探测器编号 i
            #     if event_id == param1:
            #         return ("fault", f"探测器{event_id} 未在线")
            #     # 不一致也给出可读信息，便于抓包定位
            #     return ("fault", f"探测器离线（id={event_id}, p1={param1}）")

            # 其他故障兜底
            return ("fault", f"故障事件 id=0x{event_id:02X}（p0=0x{param0:02X}, p1=0x{param1:02X}）")
        # ===================== Trig (5) =====================
        if event_type == self.Trig_Type:
            # MCU: data0==1 ? "触发" : "触发消失"
            suffix = "触发" if param0 == 0x01 else "触发消失"
            return ("info", f"{event_id}号触发{suffix}")

        # ===================== Out (6) =====================
        if event_type == self.Out_Type:
            # MCU: data1==1 ? "开启" : "关闭"
            suffix = "开启" if param1 == 0x01 else "关闭"
            return ("info", f"{event_id}号输出{suffix}")
        return ("unknown", f"未知类型记录 type=0x{event_type:02X} id=0x{event_id:02X} p0=0x{param0:02X} p1=0x{param1:02X}")

    
    def get_records(self, limit=50):
        """
        返回最近 limit 条历史记录
        """
        return self.records[-limit:]
# ----  --------------------------------------------------------------------------------------------------------


# // 历史记录类型定义
#define warning_type    1   //火灾报警类型
#define sensor_type     2   //气体报警类型
#define control_type    3   //联动类型
#define fault_type      4   //故障类型
#define trig_type       5   //触发类型
#define out_type        6   //输出类型


# void store_history_record(uint8_t type, uint8_t id, uint8_t* data) {
# 		uint8_t data_can2_send[8]={0};
# 		data_can2_send[0]=data[0];
# 		data_can2_send[1]=data[1];
# 		data_can2_send[2]=id;
# 		data_can2_send[3]=type;
#           
# 		can2_web_upload(0x10,data_can2_send,8,type);
#       
#     04 29 29 2A
# ------------------------------------------------------------------------------------------------------------


class DataStorage:
    def __init__(self):
        self.main_boards = {}  # 存储所有主板数据
        # ===== 历史落盘配置 =====
        self.history_file = "history.json"
        self._history_dirty = False
        self._history_last_flush = 0.0

    def update_data(self, frame):
        """更新数据存储"""
        main_board_id = frame['main_board_id']
        sub_board_id = frame['sub_board_id']
        frame_type = frame['frame_type']
        data = frame['data']

        # 确保主板存在
        if main_board_id not in self.main_boards:
            self.main_boards[main_board_id] = {
                'board': MainBoard(),
                'subboards': {},    # 改为字典，用子板ID作为键
                'detectors': {},    # 改为字典，用探测器ID作为键 
                'history' : History_data(),     # 加入历史数据列表
            }

        # 根据帧类型更新相应数据
        if frame_type == 0x01:  # 主板数据
            self.main_boards[main_board_id]['board'].update_from_data(frame_type, data)
            
        elif frame_type == 0x02:  # 子板数据
            # 如果子板不存在，创建新的子板
            if sub_board_id not in self.main_boards[main_board_id]['subboards']:
                self.main_boards[main_board_id]['subboards'][sub_board_id] = SubBoard()
            self.main_boards[main_board_id]['subboards'][sub_board_id].update_from_data(frame_type, data)
            
        elif frame_type in [0x03, 0x04, 0x05]:  # 探测器数据
            # 如果探测器不存在，创建新的探测器
            if sub_board_id not in self.main_boards[main_board_id]['detectors']:
                self.main_boards[main_board_id]['detectors'][sub_board_id] = Detector()
            self.main_boards[main_board_id]['detectors'][sub_board_id].update_from_data(frame_type, data)
        elif frame_type == 0x10:
            self.main_boards[main_board_id]['history'].update_from_data(data)
            self.mark_history_dirty()
            self.flush_history_to_file()   # 默认 1 秒限速写一次
        # 在更新完数据后打印所有主板信息
        '''
        print("\n=== 所有主板数据 ===")
        for board_id, board_data in self.main_boards.items():
            print(f"\n主板 {board_id}:")
            print("主板状态:", vars(board_data['board']))
            print(f"子板数量: {len(board_data['subboards'])}")
            if board_data['subboards']:
                print("子板列表:")
                for sub_id, sub in board_data['subboards'].items():
                    print(f"  子板 {sub_id}: {vars(sub)}")
            print(f"探测器数量: {len(board_data['detectors'])}")
            if board_data['detectors']:
                print("探测器列表:")
                for det_id, det in board_data['detectors'].items():
                    print(f"  探测器 {det_id}: {vars(det)}")
        print("=" * 50)
        '''

    def get_all_detector_status(self, main_board_id=None):
        """获取指定主板下的所有探测器状态
        Args:
            main_board_id: 主板ID，如果为None则获取所有主板的探测器状态
        """
        status_list = []
        
        if main_board_id is not None:
            # 获取指定主板的探测器状态
            if main_board_id in self.main_boards:
                main_board = self.main_boards[main_board_id]
                # 将字典的items转换为列表并按探测器ID排序
                sorted_detectors = sorted(main_board['detectors'].items(), key=lambda x: int(x[0]))
                
                for detector_id, detector in sorted_detectors:
                    status = {
                        'hostname': f'主机{main_board_id}',
                        'zhujiid':main_board_id,
                        'detectorId': detector_id,
                        # 状态数据 (0x03帧)
                        'signalStrength': detector.signal_strength,
                        'faultStatus': detector.fault_status,
                        'alarmLevel': detector.alarm_level,
                        'coAlarmLevel': detector.co_alarm_level,
                        'smokeAlarmLevel': detector.smoke_alarm_level,
                        'tempAlarmLevel': detector.temp_alarm_level,
                        'vocAlarmLevel': detector.voc_alarm_level,
                        'hydrogenAlarmLevel': detector.hydrogen_alarm_level,
                        # 数值数据 (0x04帧)
                        'sensorEnable': detector.sensor_enable,
                        'vocEnable': detector.voc_enable,
                        'temperature': detector.temperature,
                        'coValue': detector.co_value,
                        'smokeValue': detector.smoke_value,
                        'hydrogenValue': detector.hydrogen_value,
                        'vocValue': detector.voc_value,
                        # 警报数据 (0x05帧)
                        'tempRiseAlarm': detector.temp_rise_alarm,
                        'tempExceedAlarm': detector.temp_exceed_alarm,
                        'smokeDetected': detector.smoke_detected,
                        'smokeExceedAlarm': detector.smoke_exceed_alarm,
                        'coRiseAlarm': detector.co_rise_alarm,
                        'coExceedAlarm': detector.co_exceed_alarm,
                        'h2RiseAlarm': detector.h2_rise_alarm,
                        'h2ExceedAlarm': detector.h2_exceed_alarm,
                        'vocRiseAlarm': detector.voc_rise_alarm,
                        'vocExceedAlarm': detector.voc_exceed_alarm
                    }
                    status_list.append(status)
        else:
            # 获取所有主板的探测器状态
            for main_id, main_board in self.main_boards.items():
                # 将字典的items转换为列表并按探测器ID排序
                sorted_detectors = sorted(main_board['detectors'].items(), key=lambda x: int(x[0]))
                
                for detector_id, detector in sorted_detectors:
                    status = {
                        'hostname': f'主机{main_id}',
                        'zhujiid': main_id,
                        'detectorId': detector_id,
                        # ... 同上所有状态数据 ...
                    }
                    status_list.append(status)
                    
        return status_list

    def get_all_subboard_status(self, main_board_id=None):
        """获取指定主板下的所有子板状态
        Args:
            main_board_id: 主板ID，如果为None则获取所有主板的子板状态
        """
        status_list = []
        
        if main_board_id is not None:
            # 获取指定主板的子板状态
            if main_board_id in self.main_boards:
                main_board = self.main_boards[main_board_id]
                # 将字典的items转换为列表并按子板ID排序
                sorted_subboards = sorted(main_board['subboards'].items(), key=lambda x: int(x[0]))
                
                for sub_id, subboard in sorted_subboards:
                    status = {
                        'hostname': f'主机{main_board_id}',
                        'zhujiid': main_board_id,
                        'subboardId': sub_id,
                        'signalStrength': subboard.signal_strength,
                        'outputs': subboard.outputs,
                        'inputs': subboard.inputs
                    }
                    status_list.append(status)
        else:
            # 获取所有主板的子板状态
            for main_id, main_board in self.main_boards.items():
                # 将字典的items转换为列表并按子板ID排序
                sorted_subboards = sorted(main_board['subboards'].items(), key=lambda x: int(x[0]))
                
                for sub_id, subboard in sorted_subboards:
                    status = {
                        'hostname': f'主机{main_id}',
                        'zhujiid': main_id,
                        'subboardId': sub_id,
                        'signalStrength': subboard.signal_strength,
                        'outputs': subboard.outputs,
                        'inputs': subboard.inputs
                    }
                    status_list.append(status)
                    
        return status_list

    def get_all_mainboard_status(self, main_board_id=None):
        """获取主板状态"""
        status_list = []
        
        if main_board_id is not None:
            # 获取指定主板状态
            if main_board_id in self.main_boards:
                board = self.main_boards[main_board_id]['board']
                is_online = self.is_board_online(board)
                status = {
                    'hostname': f'主机{main_board_id}',
                    'zhujiid': main_board_id,
                    'sensorCount': board.detector_online_count,
                    'faultCount': board.fault_count,
                    'alertCount': board.alarm_count,
                    'alertLevel': board.max_alarm_level,
                    'inputs': board.inputs,
                    'outputs': board.outputs,
                    'outputs_lock': board.outputs_lock,
                    'status': '离线' if not is_online else (
                        '火警' if board.max_alarm_level >= 3 else
                        '异常' if board.fault_count > 0 else
                        '正常'
                    )
                }
                return [status]  # 返回单个状态的列表
            else:
                # 如果主机ID不存在，返回未知状态
                status = {
                    'hostname': f'主机{main_board_id}',
                    'zhujiid': main_board_id,
                    'sensorCount': 0,
                    'faultCount': 0,
                    'alertCount': 0,
                    'alertLevel': 0,
                    'inputs': [False] * 8,
                    'outputs': [False] * 8,
                    'outputs_lock': [False] * 8,
                    'status': '未知'
                }
                return [status]  # 返回单个状态的列表
        else:
            # 获取所有主板状态
            for board_id in range(1, 201):
                if board_id in self.main_boards:
                    board = self.main_boards[board_id]['board']
                    is_online = self.is_board_online(board)
                    status = {
                        'hostname': f'主机{board_id}',
                        'zhujiid': board_id,
                        'sensorCount': board.detector_online_count,
                        'faultCount': board.fault_count,
                        'alertCount': board.alarm_count,
                        'alertLevel': board.max_alarm_level,
                        'inputs': board.inputs,
                        'outputs': board.outputs,
                        'outputs_lock': board.outputs_lock,
                        'status': '离线' if not is_online else (
                            '火警' if board.max_alarm_level >= 3 else
                            '异常' if board.fault_count > 0 else
                            '正常'
                        )
                    }
                    status_list.append(status)
                else:
                    # 如果主机ID不存在，添加未知状态
                    status = {
                        'hostname': f'主机{board_id}',
                        'zhujiid': board_id,
                        'sensorCount': 0,
                        'faultCount': 0,
                        'alertCount': 0,
                        'alertLevel': 0,
                        'inputs': [False] * 8,
                        'outputs': [False] * 8,
                        'outputs_lock': [False] * 8,
                        'status': '未知'
                    }
                    status_list.append(status)

            # 修改过滤逻辑：只显示非未知状态的主机
            filtered_status_list = [
                status for status in status_list 
                if status['status'] != '未知'
            ]
            
            # 确保按主机ID排序
            filtered_status_list.sort(key=lambda x: x['zhujiid'])
            # print(filtered_status_list)
            return filtered_status_list

    def is_board_online(self, board):
        """检查主板是否在线"""
        current_time = time.time()
        return (current_time - board.last_update_time) <= 10  # 10秒内有数据更新则认为在线
    
    def get_history(self, main_board_id, limit=50):
        mb = self.main_boards.get(main_board_id)
        if not mb:
            return []
        return mb['history'].get_records(limit)
    
    def load_history_from_file(self, filepath=None):
        """
        启动时恢复历史：从 history.json 读出每个主机的 records，塞回 History_data.records
        文件格式：{"1":[rec,...], "2":[rec,...]}
        """
        import os, json

        path = filepath or self.history_file
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if not isinstance(obj, dict):
                return

            for k, records in obj.items():
                try:
                    main_id = int(k)
                except:
                    continue
                if not isinstance(records, list):
                    continue

                # 确保主板结构存在
                if main_id not in self.main_boards:
                    self.main_boards[main_id] = {
                        'board': MainBoard(),
                        'subboards': {},
                        'detectors': {},
                        'history': History_data(),
                    }

                # 直接恢复 records
                self.main_boards[main_id]['history'].records = records

        except Exception as e:
            print(f"[HISTORY] load_history_from_file failed: {e}")

    def mark_history_dirty(self):
        self._history_dirty = True

    def flush_history_to_file(self, filepath=None, min_interval_sec=1.0):
        """
        把所有主机的历史 records 落盘到 history.json
        - min_interval_sec 用于限速，避免每帧都写盘
        """
        import json, time

        if not self._history_dirty:
            return

        now = time.time()
        if min_interval_sec > 0 and (now - self._history_last_flush) < min_interval_sec:
            return

        path = filepath or self.history_file

        try:
            out = {}
            for main_id, mb in self.main_boards.items():
                hist = mb.get("history")
                if hist is None:
                    continue
                # key 用字符串，便于 JSON
                out[str(main_id)] = hist.records

            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            self._history_dirty = False
            self._history_last_flush = now

        except Exception as e:
            print(f"[HISTORY] flush_history_to_file failed: {e}")
   