import can
import logging
import json
import webview
import os
import sys
import atexit
from queue import Queue, Empty
from data_storage import DataStorage, MainBoard, History_data

import can.interfaces.pcan
import can.interfaces.pcan.pcan

IS_FROZEN = getattr(sys, "frozen", False)
Exe_Dir = os.path.dirname(sys.executable) if IS_FROZEN else os.path.abspath(".")
DATA_DIR_NAME = "data"
Data_Dir = os.path.join(Exe_Dir, DATA_DIR_NAME)
if IS_FROZEN:
    os.chdir(Exe_Dir)

if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(Exe_Dir)
    # onefile 模式下 DLL 解压到 _MEIPASS 临时目录
    _meipass = getattr(sys, "_MEIPASS", None)
    if _meipass:
        os.add_dll_directory(_meipass)


def Resource_Path(rel_path: str) -> str:
    """只读资源（HTML/JS/图片），PyInstaller 解压到 _MEIPASS。"""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)


def ensure_data_dir() -> str:
    os.makedirs(Data_Dir, exist_ok=True)
    return Data_Dir


def Data_Path(filename: str) -> str:
    """可写数据文件，落在 exe 同级 data 子目录。"""
    return os.path.join(ensure_data_dir(), filename)


def migrate_legacy_data_files():
    """兼容旧版：将 exe 同级的数据文件迁入 data 子目录。"""
    ensure_data_dir()
    for name in ("history.json", "notes.json", "app.log"):
        old_path = os.path.join(Exe_Dir, name)
        new_path = os.path.join(Data_Dir, name)
        if os.path.isfile(old_path) and not os.path.exists(new_path):
            try:
                os.replace(old_path, new_path)
            except OSError as exc:
                logging.getLogger(__name__).warning("迁移 %s 失败: %s", name, exc)


def setup_runtime_logging():
    """打包后无控制台，写入 data/app.log 便于长期运维排查。"""
    ensure_data_dir()
    handlers = [logging.StreamHandler()]
    if IS_FROZEN:
        handlers.append(
            logging.FileHandler(Data_Path("app.log"), encoding="utf-8")
        )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )


setup_runtime_logging()
logger = logging.getLogger(__name__)
DEBUG_CAN = not IS_FROZEN
CAN_QUEUE_MAX = 500

# 静音 python-can 的所有 backend 各种警告
logging.getLogger("can").setLevel(logging.CRITICAL)
logging.getLogger("can.interfaces").setLevel(logging.CRITICAL)
logging.getLogger("can.interfaces.pcan").setLevel(logging.CRITICAL)
logging.getLogger("can.interfaces.socketcan").setLevel(logging.CRITICAL)
logging.getLogger("can.interfaces.kvaser").setLevel(logging.CRITICAL)
logging.getLogger("can.detect_available_configs").setLevel(logging.CRITICAL)

class CANInterface:
    def __init__(self,data_storage=None):
        self.bus = None
        self.notifier = None
        self.reader = None
        self.is_connected = False    
        self.data_storage = data_storage
        self.pcan_info = {}
        
        # 初始化默认值，即使没有检测到PCAN设备
        self.channel = ''
        self.device_name = ''
        self.bitrate = 250000  # 默认波特率250000   
        self.interface = ''
        self.fd = False  # 默认不使用CAN FD
        
        # 探测 PCAN 设备
        self.pcan_info = self.search_pcan_devices()
        # 如果检测到PCAN设备，设置相应的参数
        if self.pcan_info:
            self.channel = self.pcan_info['Channel'] 
            self.device_name = self.pcan_info['Device_name']
            self.interface = self.pcan_info['Interface']
        
        self.data_queue = Queue()   # 用于存放接收到的 CAN 帧（已经整理成 dict）
        self.latest_frame = None   # 用于存放最新解析的 CAN 帧
        

    def search_pcan_devices(self):      # 检测可用的Pcan数量和信息
        # import os, sys, platform, ctypes, traceback

        # print(">>> ENTER search_pcan_devices")
        # print("arch:", platform.architecture())
        # print("exe:", sys.executable)
        # exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
        # print("exe_dir:", exe_dir)

        # # 1) 确保 exe 目录进入 DLL 搜索路径（必须在 import pcan 前做）
        # if hasattr(os, "add_dll_directory"):
        #     os.add_dll_directory(exe_dir)

        # # 2) 直接用 ctypes 测 PCANBasic.dll 能不能加载（一步见生死）
        # try:
        #     ctypes.WinDLL("PCANBasic.dll")
        #     print("PCANBasic.dll: LOAD OK")
        # except Exception as e:
        #     print("PCANBasic.dll: LOAD FAIL ->", repr(e))
        #     print("HINT: 这基本就是位数/依赖/DLL路径问题")
        #     traceback.print_exc()

        # # 3) 强制导入 python-can 的 pcan 后端（避免冻结裁剪/注册不到）
        # try:
        #     import can
        #     print("python-can version:", can.__version__)
        #     import can.interfaces.pcan
        #     import can.interfaces.pcan.pcan
        #     print("pcan backend import: OK")
        # except Exception as e:
        #     print("pcan backend import: FAIL ->", repr(e))
        #     traceback.print_exc()

        # # 4) 再探测一次
        # try:
        #     import can
        #     configs = can.detect_available_configs()
        #     print("PCAN configs:", configs)
        # except Exception as e:
        #     print("detect_available_configs FAIL ->", repr(e))
        #     traceback.print_exc()

        # return []
    

    # ============================================================================
        configs = can.detect_available_configs() # 获取CAN接口的配置信息
        pcan_configs = [cfg for cfg in configs if cfg.get("interface") == "pcan"] # 过滤出PCAN接口的配置信息               
        # print(type(pcan_configs))
        # pcan_configs里是列表里嵌套字典
        """
        pcan_configs字典第一个Pcan默认设置是
        interface: pcan
        channel: PCAN_USBBUS1
        supports_fd: False
        fd: False
        controller_number: 0
        device_id: 255
        device_name: PEAK-System PCAN USB
        device_type: 5
        channel_condition: 2
        """
        self.pcan_info = {}             # 先放一个空字典
        if(len(pcan_configs))==0:       # 如果没有检测到pcan设备直接返回空列表
            self.channel = ''
            self.device_name = ''
            self.interface = ''
            return self.pcan_info
        elif(len(pcan_configs))==1:     # 如果检测到一个pcan设备就返回这个设备的信息
            self.pcan_info['Device_name'] = pcan_configs[0]['device_name']
            self.pcan_info['Channel'] = pcan_configs[0]['channel']
            self.pcan_info['Interface']= pcan_configs[0]['interface']
            self.device_name = self.pcan_info['Device_name']
            self.channel = self.pcan_info['Channel']
            self.interface = self.pcan_info['Interface']
            # print(f"pcan_list",pcan_list)
            return self.pcan_info
        else:
            raise RuntimeError(
                f"检测到{len(pcan_configs)}个 PCAN 设备，请只保留一个再重试："
            )

    def connect(self):
        # 直接判断一下有没有探测到 PCAN：
        if not self.pcan_info:
            return {"status": "Error", "error": "未检测到 PCAN 设备，无法连接"}
        """连接到 PCAN 设备"""
        try:
            if self.is_connected:           #self.is_connected 初始值是 False
                return {"status": "Error", "error": "已经连接到 PCAN 设备"}
            
            # 使用 python-can 库连接到 PCAN 设备
            self.bus = can.Bus(
                channel=self.channel,
                interface=self.interface,
                bitrate=self.bitrate,
                fd=self.fd
            )
            self.is_connected = True
            # --------------------------------------第一个print-----------
            print(f"已连接到 PCAN 设备: {self.device_name}，通道: {self.channel}，波特率: {self.bitrate},Pcan已连接")
            
            # 启动CAN消息监听
            self.start_notifier()
            
            return {"status": "Connected"}
        except Exception as e:
            return {"status": "Error", "error": str(e)}

    def disconnect(self):               # 断开与 PCAN 设备的连接
        print(f" 开始断开CAN连接，当前状态：is_connected={self.is_connected}, notifier={self.notifier}, bus={self.bus}")
        try:
            # 无论是否连接，都尝试关闭资源
            if self.notifier:
                print("DEBUG: 停止Notifier")
                self.notifier.stop()        # 停止Notifier
                self.notifier = None        # 清空notifier引用
            if self.bus:
                print("DEBUG: 关闭Bus")
                self.bus.shutdown()         # 关闭总线连接
                self.bus = None             # 清空bus引用
            print(f"DEBUG: 已断开与 PCAN 设备: {self.device_name} 的连接")
            return {"status": "Disconnected"}
        except Exception as e:
            print(f"DEBUG: 断开CAN连接时发生异常: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "Error", "error": str(e)}
        finally:
            # 重置所有状态
            # 不管上面有没有抛异常，都强制认为逻辑上“别再用这个连接了”
            self.is_connected = False
            self.reader = None
    
    def start_notifier(self):   # 启动通知器以接收 CAN 帧
        """启动 CAN 消息监听（异步接收线程）"""
        if not self.is_connected:
            print("PCAN 未连接，无法启动 Notifier")
            return {"status": "Error", "error": "PCAN 未连接"}
        if self.notifier is not None:
            print("Notifier 已经在运行了")
            return {"status": "Error", "error": "Notifier 已经在运行"}
        try:
            # 启动Notifier
            # self.notifier = can.Notifier(self.bus, [回调函数])
            # 回调函数在收到CAN消息时被调用
            self.notifier = can.Notifier(self.bus, [self.on_can_msg])
            #----------------------------------------------第二个print-----------
            print("Notifier 已启动，开始接收 CAN 帧")
            # print(f"DEBUG: Notifier对象: {self.notifier}")
            
            # 检查Notifier的状态
            if hasattr(self.notifier, 'running'):
                print(f"DEBUG: Notifier运行状态: {self.notifier.running}")
            return {"status": "Connected"}
        except Exception as e:
            print(f"DEBUG: 启动Notifier异常: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "Error", "error": str(e)}



  #------------------------------------------------------------------------------------------------------------------------------------------------      
    def on_can_msg(self, msg):# 接收层：CAN 收到一帧 msg 时自动回调
        if DEBUG_CAN:
            logger.debug("收到CAN帧: %s", msg)
        parsed = self._parse_can_frame(msg)
        if parsed is not None:
            if DEBUG_CAN:
                logger.debug("解析后的CAN帧: %s", parsed)
            self.process_parsed_frame(parsed)
        elif DEBUG_CAN:
            logger.debug("CAN帧解析失败: %s", msg)

    def _parse_can_frame(self, msg): #解析CAN的信号了
        #  0x 手动加16进制的前缀
        #  {msg.arbitration_id:08X} → 格式化成 8 位的十六进制（大写） 
        #  0  不足补零
        #  8 总宽度8位
        #  X 十六进制大写
        # --------------------------------------第三个print---------------
        print(f"开始解析CAN帧: ID=0x{msg.arbitration_id:08X}, DLC={msg.dlc}, 数据={[hex(b) for b in msg.data]}, 扩展ID={msg.is_extended_id}")
        # 1）过滤错误帧 / 远程帧
        if msg.is_error_frame or msg.is_remote_frame:
            print(f"DEBUG: 过滤错误帧/远程帧")
            return None   
        # 2）保证长度 = 8
        if msg.dlc != 8:
            print(f"DEBUG: 帧长度不等于8，跳过")
            return None 
        # 3）解析 ID：cmd | board_id | 0xF5 | ex_id
        #  CAN ID 是32bit的 | cmd(8bit) | board_id(8bit) | fixed(8bit) | ex_id(8bit) |
        can_id = msg.arbitration_id
        cmd     = (can_id >> 24) & 0xFF
        board_id= (can_id >> 16) & 0xFF
        fixed   = (can_id >> 8)  & 0xFF
        ex_id   = can_id & 0xFF

        print(f"解析ID: cmd=0x{cmd:02X}, board_id=0x{board_id:02X}, fixed=0x{fixed:02X}, ex_id=0x{ex_id:02X}")
        
        # 固定帧的判断
        if fixed != 0xF5:
            print(f"DEBUG: 固定字节不是0xF5，跳过")
            return None

        # 4）解析数据部分
        if len(msg.data) != 8:
            print(f"DEBUG: 数据长度不等于8，跳过")
            return None
        data_list = list(msg.data)
        print(f"解析数据，数据列表: {[hex(b) for b in data_list]}")

        # # 这里直接转成 “0xXX” 字符串
        # frame = {
        #     'frame_type'    : f"0x{cmd:02X}",
        #     'main_board_id' : f"0x{board_id:02X}",
        #     'sub_board_id'  : f"0x{ex_id:02X}",
        #     'data'          : [f"0x{b:02X}" for b in data_list],
        # }

        frame = {
            'frame_type': cmd,          # int，例如 0x01
            'main_board_id': board_id,  # int，例如 0x05
            'sub_board_id': ex_id,      # int，例如 0x01
            'data': data_list           # [int, int, ...]
        }
        return frame



    
    def get_all_mainboard_status(self):
        """获取所有主板状态"""
        return self.data_storage.get_all_mainboard_status()
    def get_all_subboard_status(self, main_board_id):
        """获取指定主板的子板状态"""
        try:
            print(f"正在获取主板 {main_board_id} 的子板状态")
            result = self.data_storage.get_all_subboard_status(main_board_id)
            print(f"获取到的探测器数据: {result}")
            return result
        except Exception as e:
            logging.error(f"获取探测器状态失败: {str(e)}")
            print(f"获取探测器状态失败: {str(e)}")
            return []
    def get_all_detector_status(self, main_board_id):
        """获取指定主板的探测器状态"""
        try:
            print(f"正在获取主板 {main_board_id} 的探测器状态")
            result = self.data_storage.get_all_detector_status(main_board_id)
            print(f"获取到的探测器数据: {result}")
            return result
        except Exception as e:
            logging.error(f"获取探测器状态失败: {str(e)}")
            print(f"获取探测器状态失败: {str(e)}")
            return []
    def process_parsed_frame(self, parsed):#接收解析层的数据(parsed)，更新最新状态，并入队
        # 1）更新最新帧（应用层最重要的功能）
        self.latest_frame = parsed
         # 2）喂给 DataStorage（如果有
        if self.data_storage is not None:
            print(f"更新DataStorage: {parsed}")
            print(f"----------------------------------------------------------------结束解析--------------------------------------------------------------------")

            self.data_storage.update_data(parsed)
        # 3）入队，让其他线程/UI 可以取（限制队列长度，防止长期运行内存膨胀）
        while self.data_queue.qsize() >= CAN_QUEUE_MAX:
            try:
                self.data_queue.get_nowait()
            except Empty:
                break
        self.data_queue.put(parsed)
    
    def send_can_frame(self, main_board_id, msg_type, data):
        """按 STM32 网页控制协议发送 CAN 扩展帧。

        ExtId 高字节为 msg_type；Data[0]/Data[1] 为控制参数。
        """
        if not self.is_connected or self.bus is None:
            return {'status': 'Error', 'message': 'PCAN 未连接，无法发送命令'}
        try:
            payload = list(data[:8]) + [0x00] * 8
            payload = payload[:8]
            can_id = (msg_type << 24) | (main_board_id << 16) | (0xF5 << 8)
            msg = can.Message(
                arbitration_id=can_id,
                data=payload,
                is_extended_id=True,
            )
            self.bus.send(msg)
            print(
                f"发送CAN控制: id=0x{can_id:08X}, "
                f"msg_type=0x{msg_type:02X}, data={[hex(b) for b in payload]}"
            )
            return {'status': 'OK'}
        except Exception as e:
            print(f"发送CAN控制命令失败: {e}")
            return {'status': 'Error', 'message': str(e)}

    def send_web_control(self, main_board_id, command, param1=0, param2=0):
        """STM32 网页 CAN 控制协议封装。

        msg_type 0x00: 锁控制 web_control_lock(Data[0], 1-Data[1])
        msg_type 0x01: 网页触发 web_trig(Data[0], Data[1])
        msg_type 0x02: 系统状态 Data[0]=0手动/1自动/2灭火器开/3灭火器关/6复位
        """
        command = str(command).lower()
        if command == 'manual':
            return self.send_can_frame(main_board_id, 0x02, [0x00, 0x00])
        if command == 'auto':
            return self.send_can_frame(main_board_id, 0x02, [0x01, 0x00])
        if command == 'fire_on':
            return self.send_can_frame(main_board_id, 0x02, [0x02, param1 & 0xFF])
        if command == 'fire_off':
            return self.send_can_frame(main_board_id, 0x02, [0x03, param1 & 0xFF])
        if command == 'reset':
            return self.send_can_frame(main_board_id, 0x02, [0x06, 0x00])
        if command == 'lock':
            return self.send_can_frame(main_board_id, 0x00, [param1 & 0xFF, param2 & 0xFF])
        if command == 'trigger':
            return self.send_can_frame(main_board_id, 0x01, [param1 & 0xFF, param2 & 0xFF])
        return {'status': 'Error', 'message': f'未知控制命令: {command}'}

    def send_control_command(self, main_board_id, output_num, new_status):
        """发送控制命令到 CAN 总线（兼容旧前端继电器/模式接口）。"""
        if output_num == 9:
            command = 'auto' if new_status else 'manual'
            return self.send_web_control(main_board_id, command)
        lock_id = output_num - 1
        lock_state = 0x00 if new_status else 0x01
        return self.send_web_control(main_board_id, 'lock', lock_id, lock_state)
    




# if __name__ == "__main__":
#     can_interface = CANInterface()              #can初始化
#     connect_result = can_interface.connect()    #连接pcan设备
#     if connect_result['status'] == "OK":        #连接成功
#         print("开始接收CAN数据，按 Ctrl+C 停止...")
#         try:
#             while True:
#                 if not can_interface.data_queue.empty():
#                     frame = can_interface.data_queue.get()
#                     # print(f"Received CAN Frame: {frame}")
#         except KeyboardInterrupt:
#             print("Stopping CAN interface...")
#         finally:
#             can_interface.disconnect()
#     else:
#         print(f"Failed to connect to PCAN device: {connect_result['error']}")

class Can_Api():
    def __init__(self):
        migrate_legacy_data_files()
        self.history_file = Data_Path("history.json")
        self.notes_file = Data_Path("notes.json")

        self.data_storage = DataStorage()
        self.data_storage.history_file = self.history_file
        self.data_storage.load_history_from_file(self.history_file)

        self.can_interface = CANInterface(data_storage=self.data_storage)
        self.notes = self._load_notes()
        self.current_port = None
        self._shutdown_done = False
        atexit.register(self.shutdown)
        logger.info("应用启动，数据目录: %s", ensure_data_dir())

    def shutdown(self):
        """退出时落盘并释放 CAN，供窗口关闭 / atexit 调用。"""
        if self._shutdown_done:
            return
        self._shutdown_done = True
        try:
            self.data_storage.flush_history_to_file(self.history_file, min_interval_sec=0)
        except Exception as e:
            logger.error("退出时保存历史失败: %s", e)
        try:
            if self.can_interface.is_connected:
                self.can_interface.disconnect()
        except Exception as e:
            logger.error("退出时断开 CAN 失败: %s", e)
        logger.info("应用已安全退出")

    def _load_notes(self):                  #加载保存的笔记
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"title": "", "content": ""}
        return {"title": "", "content": ""}
    def save_notes(self, title, content):
        """保存笔记"""
        try:
            notes = {"title": title, "content": content}
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
            self.notes = notes
            return {"status": "success"}
        except Exception as e:      
            logging.error(f"保存笔记失败: {str(e)}")
            return {"status": "error", "message": str(e)}
    def get_notes(self):                    #获取保存的笔记
        return self.notes
    def search_pcan_devices(self):          #搜索可用串口
        return self.can_interface.search_pcan_devices()
    def connect_can(self):                  #"""前端调用：连接 PCAN"""
        result = self.can_interface.connect()  # 就是 connect() 里返回的那个 dict
        if result["status"] == "Connected":
           self.current_port =  self.can_interface.pcan_info['Channel']
        return {
            "status": result["status"],
            "pcan_info": self.can_interface.pcan_info,
            "is_connected": self.can_interface.is_connected,   # 新增
            "error": result.get("error"),
        }
    
    def disconnect_can(self):               #  """前端调用：断开 PCAN"""
        result = self.can_interface.disconnect()
        return{
            "status": result["status"],
            "is_connected":self.can_interface.is_connected,
            "current_port": None
        }


    def get_can_status(self):               #"""前端调用：查看连接状态 + 设备信息"""
        return {
            "is_connected": self.can_interface.is_connected,
            "pcan_info": self.can_interface.pcan_info
        }

    def getHostProblem(self,hostStatus):
        
        # 过滤出有问题的 host
        hostProblemsX = [
            host for host in hostStatus
            if host.get('faultCount', 0) > 0 or host.get('alertLevel', 0) > 0 or host.get('alertCount', 0) > 0
        ]
        
        #filtered_status_list = [status for status in status_list if status['status'] != '离线']

        hostProblems = []

        # 更新问题描述
        for problem in hostProblemsX:
            descriptions = []
            
            # 如果有火警，添加火警描述
            if problem.get('alertLevel', 0) > 0:
                descriptions.append(f'最高警报级别{problem["alertLevel"]}')
            
            # 如果有警报，添加警报描述
            if problem.get('alertCount', 0) > 0:
                descriptions.append(f'出现{problem["alertCount"]}个警报')
            
            # 如果有故障，添加故障描述
            if problem.get('faultCount', 0) > 0:
                descriptions.append(f'出现{problem["faultCount"]}个故障')
            
            # 合并所有描述
            problem['problem'] = '；'.join(descriptions)
            
            # 设置问题的严重程度（用于颜色显示）
            problem['severity'] = 'alert' if problem.get('alertLevel', 0) > 0 else 'fault'
            
            # 检查是否已查看
            # problem['viewed'] = (problem['hostname'] + problem['problem']) in viewed_problems
                        
            hostProblems.append(problem)
            
        return hostProblems
    
    def getFaults(self,detectors):  # 获得探测器的各种报错
        
        faults = []
        for detector in detectors:

            if detector['faultStatus'] == 3:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '硬件故障'
                })

            if detector['alarmLevel'] > 0:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': f'警报级别: {detector["alarmLevel"]}'
                })

            if detector['coAlarmLevel'] > 0:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': f'CO警报级别: {detector["coAlarmLevel"]}'
                })

            if detector['smokeAlarmLevel'] > 0:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': f'烟雾级别: {detector["smokeAlarmLevel"]}'
                })

            if detector['tempAlarmLevel'] > 0:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': f'温度级别: {detector["tempAlarmLevel"]}'
                })

            if detector['vocAlarmLevel'] > 0:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': f'VOC级别: {detector["vocAlarmLevel"]}'
                })

            if detector['hydrogenAlarmLevel'] > 0:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': f'氢气级别: {detector["hydrogenAlarmLevel"]}'
                })

            # 添加警报数据 (0x05帧)
            if detector['tempRiseAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '温度上升警报'
                })

            if detector['tempExceedAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '温度超标警报'
                })

            if detector['smokeDetected']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '检测到烟雾'
                })

            if detector['smokeExceedAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '烟雾超标警报'
                })

            if detector['coRiseAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': 'CO上升警报'
                })

            if detector['coExceedAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': 'CO超标警报'
                })

            if detector['h2RiseAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '氢气上升警报'
                })

            if detector['h2ExceedAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': '氢气超标警报'
                })

            if detector['vocRiseAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': 'VOC上升警报'
                })

            if detector['vocExceedAlarm']:
                faults.append({
                    'name': f'探测器{detector["detectorId"]}',
                    'description': 'VOC超标警报'
                })
                
        
        # faults.append({
        #             'name': f'探测器4',
        #             'description': 'VOC超标警报'
        #         })
                
        return faults

    def get_all_hosts(self):
        whole = {}
        whole['hostStatus'] = self.can_interface.data_storage.get_all_mainboard_status()
        #print(777,whole['hostStatus'])
        whole['hostProblems'] = self.getHostProblem(whole['hostStatus']) #有问题 swgao ['主机错误xxx'] #
        #print(222,whole)
        return whole

    def get_host_data(self, hid):
        # 取出指定hid主机的所有数据信息
        host_data = self.can_interface.data_storage.get_all_mainboard_status(hid)
        if not host_data:               #做host_data[0]的空检查
            return {}  # 或者返回一个带错误信息的结构
        xhost = host_data[0]            # ★★ 把这一行加回来

          # 现在确保有数据才访问[0]
        selectedHostInfo = {}
        selectedHostInfo['onlineSensors'] = int(xhost['sensorCount'])
        selectedHostInfo['problemCount'] = int(xhost['faultCount']) + int(xhost['alertCount'])
        selectedHostInfo['alertLevel'] = int(xhost['alertLevel'])        
        
        detectors = self.can_interface.data_storage.get_all_detector_status(hid)

        for detector in detectors:
            detector['name'] = f'探测器{detector["detectorId"]}'  
            detector['signal'] = f'{detector["signalStrength"]}'            
            detector['temperature'] = f'{max(detector["temperature"]-40, 0)}℃'  
            detector['co'] = f'{detector["coValue"]*0.1}ppm'     
            detector['smoke'] = f'{(detector["smokeValue"]*0.001):.3f}dbm'  
            detector['voc'] = f'{detector["vocValue"]*10}ppm'     
            detector['hydrogen'] = f'{detector["hydrogenValue"]*10}ppm'         
                                                 
        currentHostFaults = self.getFaults(detectors)
        # 追加：从历史记录里把“手动报警”同步到中间栏
        hist = self.data_storage.get_history(hid, limit=50)
        if any((r.get("level") == "warning") and ("手动报警" in r.get("message", "")) for r in hist):
            currentHostFaults.insert(0, {
                "name": "主机",
                "description": "手动报警触发"
            }) 
        # 新增：把历史里的故障、报警同步到中间栏
        for r in hist:
            if r.get("level") == "fault":
                currentHostFaults.append({"name": "故障", "description": r.get("message", "")})
            elif r.get("level") == "warning" and "手动报警" not in r.get("message", ""):
                currentHostFaults.append({"name": "警报", "description": r.get("message", "")})  

        # 顶部总数
        selectedHostInfo["problemCount"] = len(currentHostFaults)

        # print(111,currentHostFaults)
        
        host = {}
        host['selectedHostInfo'] = selectedHostInfo
        host['detectors'] = detectors
        #host['subboards'] = self.serial_interface.data_storage.get_all_subboard_status(hid)     #subboards; #
        subboards = self.can_interface.data_storage.get_all_subboard_status(hid)     #subboards; #
        
        for subboard in subboards:
            subboard['id'] = f'分区控制器{subboard["subboardId"]}'  
            subboard['signal'] = f'{subboard["signalStrength"]}'      
            
        host['subboards'] = subboards
        #print(666,host['subboards'])
        host['currentHostFaults'] = currentHostFaults
        host['outputsStatus'] =  xhost['outputs']#[1,0,1,1,1,0,1,1]#
        host['outputslockStatus'] = xhost['outputs_lock']#[1,1,1,1,1,1,1,1]#
        host['dcControlStatus'] = xhost['outputs']#[1,0,1,1,1,1,0,1]#          #???????
        host['inputsStatus'] = xhost['inputs']#[1,1,1,0,1,1,1,1]#
        
        #print(444,xhost['outputs'])
        
        return host

    def get_mainboard_status(self):
        """获取所有主板状态"""
        return self.can_interface.get_all_mainboard_status()
    def get_subboard_status(self, main_board_id):
        """获取所有子板状态"""
        return self.can_interface.get_all_subboard_status(main_board_id)
    def get_detector_status(self, main_board_id):
        """获取所有探测器状态"""
        return self.can_interface.get_all_detector_status(main_board_id)

    def control_dc(self, hostid, switch_number, status):
        """
        前端点击控制开关时调用

        hostid         : 主机ID（主板ID）
        switch_number  : 1~8 表示继电器输出编号，9 表示自动/手动模式
        status         : True / False
        """
        try:
            result = self.can_interface.send_control_command(
                main_board_id=hostid,
                output_num=switch_number,
                new_status=status
            )

            if result.get("status") not in ("OK", "Connected"):
                return {
                    "status": "error",
                    "message": result.get("message", "发送 CAN 控制命令失败")
                }

            return {"status": "success"}

        except Exception as e:
            logging.error(f"控制输出失败: {e}")
            return {"status": "error", "message": str(e)}

    def send_host_control(self, hostid, command, param1=0, param2=0):
        """前端主机控制面板：按 STM32 网页 CAN 协议下发命令。"""
        try:
            result = self.can_interface.send_web_control(
                main_board_id=hostid,
                command=command,
                param1=param1,
                param2=param2,
            )
            if result.get("status") != "OK":
                return {
                    "status": "error",
                    "message": result.get("message", "发送 CAN 控制命令失败"),
                }
            return {"status": "success"}
        except Exception as e:
            logging.error(f"主机控制失败: {e}")
            return {"status": "error", "message": str(e)}


    def get_latest_frame(self):
        """
        前端调用：拿一帧最新数据。
        优先从队列里取一帧；如果没有，就返回 None
        """
        try:
            frame = self.can_interface.data_queue.get_nowait()
            return {
                "has_frame": True,
                "frame": frame
            }
        except Empty:
            # 队列空
            return {
                "has_frame": False,
                "frame": None
            }
    #下面有 control_dc 
    # def send_control(self, main_board_id, output_num, new_status):
    #     return self.can_interface.send_control_command(main_board_id, output_num, new_status)
    
    # === 如果要用 pywebview + Vue，就这样写 main ===
    
    
    def get_history(self, main_board_id=0, limit=50):
        """
        给前端用：返回最近 limit 条 history
        """
        if not self.data_storage:
            return []

        records = self.data_storage.get_history(main_board_id, limit)

        # 确保可 JSON 序列化：time/level/message/raw 都是基础类型即可
        return records

    def load_history_file(self, main_board_id, limit=200):
        """前端读取本地历史缓存（实际由后端 data_storage 统一管理）。"""
        return self.data_storage.get_history(main_board_id, limit)

    def save_history_file(self, main_board_id, records):
        """前端合并历史后回写：更新内存并落盘到 exe 目录。"""
        try:
            if main_board_id not in self.data_storage.main_boards:
                self.data_storage.main_boards[main_board_id] = {
                    'board': MainBoard(),
                    'subboards': {},
                    'detectors': {},
                    'history': History_data(),
                }
            self.data_storage.main_boards[main_board_id]['history'].records = records or []
            self.data_storage.mark_history_dirty()
            self.data_storage.flush_history_to_file(self.history_file, min_interval_sec=0)
            return {"status": "success"}
        except Exception as e:
            logger.error("save_history_file 失败: %s", e)
            return {"status": "error", "message": str(e)}

    def search_serial_ports(self):
        # Vue 还是叫 search_serial_ports，其实内部去查 PCAN
        return self.search_pcan_devices()
    def connect_serial_port(self, port_name=None):
        # CAN 不需要前端选端口，忽略参数即可
        return self.connect_can()

    def disconnect_serial_port(self):
        return self.disconnect_can()

    def get_connection_status(self):
        return self.get_can_status()

if __name__ == "__main__":
    api = Can_Api()
    html_path = Resource_Path(os.path.join("base", "www", "index.html"))
    if not os.path.exists(html_path):
        logger.error("前端资源缺失: %s", html_path)
        raise SystemExit(1)

    window = webview.create_window(
        '百安消防主站控制系统',
        html_path,
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
    )

    def on_closed():
        api.shutdown()

    window.events.closed += on_closed

    # 打包 exe 长期运行：使用 Edge 内核、关闭调试端口
    webview.start(debug=not IS_FROZEN, gui='edgechromium')
    
    
    