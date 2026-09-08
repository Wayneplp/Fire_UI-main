//将python函数整体导入，要用window判断是否存在这个变量
var api; // 先留一个全局变量，等window.pywebview.api出现了，将其赋值给api，之后全文件统一用api.xxx()调用python

var appStarted = false;

function bootApp() {
	if (appStarted) return;
	if (typeof pywebview === "undefined" || !pywebview.api) {
		console.log("启动失败：pywebview.api 未就绪");
		return;
	}
	appStarted = true;
	console.log("启动成功");
	api = window.pywebview.api;
		
		// 从 ElementPlus 中解构出 ElMessage
		const { ElMessage } = ElementPlus;
		
		const app = Vue.createApp({

			setup() {
				// 1) 新增一个历史记录 ref
				const currentHostHistory = Vue.ref([]);
				// 0. 几个子页面信息
				const currentPage = Vue.ref('can');  // 当前页面：serial/hostSelect/hostControl
				const dialogVisible = Vue.ref(false); // 是否显示对话框
				const controlPanelVisible = Vue.ref(false); // 主机控制面板
				const fireExtinguisherStatus = Vue.ref([null, null]); // null=未知, true=开, false=关
				
				// ========================================================================
				// 1. 实际上是主机 子设备 及 各种报警列表
				const hostStatus = Vue.ref([]);				
				
				// 2. 其实是主机报警信息 -swgao
				const hostProblems = Vue.ref([]);
				// ========================================================================

				// ========================================================================	
				// 详细页面中
				// 3. 选择的X号主机信息
				const selectedHostInfo = Vue.ref(null);
				
				// 4. 探测器数据
				const detectors = Vue.ref([]);				
				
				// 5. 分区探测子板数据
				const subboards = Vue.ref([]); // 存储子板数据
				
				// 6. 报警信息列表
				const currentHostFaults = Vue.ref([]);
				
				// 7. 主板警报输出
				const dcControlStatus = Vue.ref(Array(8).fill(false));
				const isAutoMode = Vue.ref(true);  // 初始化为false或根据需要的默认值	

				// 8. 自动时，主板当前IO输出状态
				const outputsStatus = Vue.ref(null);
				
				// 9. 当前主机IO输入报警状态
				const inputsStatus = Vue.ref(null);				
				// ========================================================================
				
				const historyCache = Vue.ref({}); // { [hid]: list }

				// ========================================================================
				// 临时变量
				// 新增输出状态锁数组
				const outputslockStatus = Vue.ref(null);
				
				// 故障数据（结构体）
				const faults = Vue.ref({});	
				
				const updateTimer = Vue.ref(null);
				// 在 setup() 中添加已查看问题的记录？？？？
				const viewedProblems = Vue.ref(new Set());			
				const serialPorts = Vue.ref({});
				const selectedPort = Vue.ref('');
				const isConnected = Vue.ref(false);
				const onlineHosts = Vue.ref([]);
				const selectedHost = Vue.ref(null);
				const noteTitle = Vue.ref('');
				const noteContent = Vue.ref('');				
				// ========================================================================

				//========================================================================
				// 将原始故障类型列表重命名为 faultTypes
				const faultTypes = ['探测器离线','温度传感器异常','烟感传感器异常','CO传感器异常','VOC传感器异常','氢气传感器异常','通信故障','电源故障'];
				
				



				// 2) 类型映射：把 0x10 的 type/level 转成你右侧表“故障类型”想显示的字
				const HistoryTypeText = (rec) => {
					// rec.type 是历史记录类型：1~6（warning/sensor/control/fault/trig/out）
					// rec.level 是后端解码出来的字符串（fault/warning/info/unknown...）
					const typeMap = {
						1: "火警/报警",
						2: "气体报警",
						3: "联动",
						4: "故障",
						5: "触发",
						6: "输出",
					};
					// 优先用 type（更稳定），缺省再用 level
					if (rec && typeof rec.type === "number" && typeMap[rec.type]) return typeMap[rec.type];
					if (rec && rec.level) return String(rec.level);
					return "未知";
					};





				const getRowClassName = ({ row }) => {
					// 只对主机状态表使用此样式
					return row.hasOwnProperty('status') ? `status-${row.status}` : '';
				};
				
				// 新增设置主机状态颜色的方法
				const getStatusColor = (status) => {
					if (status === '正常') return 'green';
					if (status === '异常') return 'orange';
					if (status === '火警') return 'red';
					if (status === '离线') return 'grey';
					return 'black'; // 默认颜色
				};
				
				// 修改获取问题文本颜色的方法
				const getProblemTextColor = (problem) => {
					// 如果已查看，显示灰色
					if (problem.viewed) {
						return 'grey';
					}
					
					// 未查看的问题，根据问题类型显示颜色，不考虑主机是否在线
					if (problem.alertLevel >= 3) {
						return 'red';   		// 有火警显示红色
					}
					if (problem.faultCount > 0) {
						return 'orange';  		// 有故障显示橙色
					}
					return '#fff';  			// 默认颜色
				};				
				// ========================================================================


				// ========================================================================
				const searchSerialPorts = async () => {
					console.log("CLICK: search pcan");
					try {
						// 后端返回的就是那坨字典：
						// { Device_name: "...", Channel: "...", Interface: "..." }
						const info = await api.search_serial_ports();
						console.log("搜索到的 PCAN 信息:", info);

						// 判空
						if (!info || !info.Device_name) {
							serialPorts.value = {};
							selectedPort.value = '';
							ElMessage.warning("未检测到 PCAN 设备");
							return;
						}

						// 整理成适合 v-for 的结构：
						// serialPorts = { "PCAN-USB": { Device_name, Channel, Interface } }
						serialPorts.value = {
							[info.Device_name]: info
						};

						// 默认选中这个设备（用设备名做 value）
						selectedPort.value = info.Device_name;

					} catch (error) {
						console.error(error);
						ElMessage.error("搜索 CAN 失败");
					}
				};
				
				const connectSerialPort = async () => {
					console.log("connectSerialPort 链接")
					console.log("selectedPort.value", selectedPort.value)
					try {
						const result = await api.connect_serial_port(selectedPort.value);
						console.log("connectSerialPort 链接", result)
						if (result.status === 'Connected'|| result.status === 'OK') {
							// ① 标记已连接
							if (typeof result.is_connected !== "undefined") {
								isConnected.value = !!result.is_connected;
							} else {
								await getConnectionStatus();
							}

							// ② 关闭弹窗 / 切页面
							dialogVisible.value = false;
							currentPage.value = 'hostSelect';

							// ③ ★关键：连接成功后，才启动定时刷新 ★
							startAutoRefresh();

							ElementPlus.ElMessage.success("CAN连接成功");
							
						} else {
							ElementPlus.ElMessage.error("连接失败: " + (result.error || "unknown"));
							isConnected.value = false;
						}
					} catch (error) {
						console.error("连接CAN失败:", error);
						ElementPlus.ElMessage.error("连接CAN失败");
						isConnected.value = false;
					}
				};		
				const resetUiState = () => {
					// 1) 先停掉所有定时器，否则会立刻又刷新回去
					if (updateTimer.value) {
						clearInterval(updateTimer.value);
						updateTimer.value = null;
					}

					// 2) 清空连接与下拉框
					serialPorts.value = {};
					selectedPort.value = '';
					isConnected.value = false;

					// 3) 清空主页数据（index.html 的表）
					hostStatus.value = [];
					hostProblems.value = [];

					// 4) 清空详情页数据（detail.html 的表/状态）
					selectedHostInfo.value = null;
					detectors.value = [];
					subboards.value = [];
					currentHostFaults.value = [];
					// 如果你已经加了历史记录数组，这里也清掉
					if (typeof currentHostHistory !== 'undefined') currentHostHistory.value = [];

					outputsStatus.value = null;
					outputslockStatus.value = null;
					dcControlStatus.value = Array(8).fill(false);
					inputsStatus.value = null;
					isAutoMode.value = true;

					// 5) 其它 UI 状态（可选，但建议一起清）
					onlineHosts.value = [];
					selectedHost.value = null;
					faults.value = {};
					viewedProblems.value = new Set();
					noteTitle.value = '';
					noteContent.value = '';

					// 6) 清空中转 xhr（避免误用旧数据）
					xhr.value = {};
					};



				const disconnectSerialPort = async () => {
					try {
						const result = await api.disconnect_serial_port();
						if (result.status === 'Disconnected') {
							// 1) 全部 UI 清空
							resetUiState();
							// 2) 回到连接页
							currentPage.value = 'serial';
							ElementPlus.ElMessage.success("CAN已断开");

							// 3) 重新识别设备（让下拉框重新扫描）
							await searchSerialPorts();
						} else {
							ElementPlus.ElMessage.error("断开失败: " + result.error);
						}
					} catch (error) {
						ElementPlus.ElMessage.error("断开CAN失败");
						isConnected.value = true;
					}
				};				
				
				// 新增 toggleConnect 函数
				const toggleConnect = async () => {
					if (isConnected.value) {
						await disconnectSerialPort();
					} else {
						await connectSerialPort();
					}
				};

				searchSerialPorts();
				// ========================================================================

// 修改处理控制按钮点击的函数
				const handleDCControl = async (number) => {
						if (!selectedHost.value) {
							ElMessage.warning("请先选择主机");
							return;
						}
						// 如果是第9个按钮，切换自动/手动模式
						if (number == 9) {
							const newStatus = !isAutoMode.value;
							const result = await api.control_dc(selectedHost.value, number, newStatus);
							if (result.status === 'success') {
								isAutoMode.value = newStatus;
							} else {
								ElMessage.error(result.message || "模式切换失败");
							}
						} else {
							// 1-8号按钮的处理逻辑
							const buttonIndex = number - 1;
							const newStatus = !dcControlStatus.value[buttonIndex];
							const result = await api.control_dc(selectedHost.value, number, newStatus);
							if (result.status !== 'success') {
								ElMessage.error(result.message || "控制失败");
								return;
							}
							dcControlStatus.value[buttonIndex] = newStatus;
							if (outputsStatus.value) {
								outputsStatus.value[buttonIndex] = newStatus;
							}
						}
				};

				const getFireStatusText = (index) => {
					const status = fireExtinguisherStatus.value[index];
					if (status === true) return '开启';
					if (status === false) return '关闭';
					return '未知';
				};

				const sendHostControl = async (command, param1 = 0, param2 = 0) => {
					if (!selectedHost.value) {
						ElMessage.warning("请先选择主机");
						return { status: 'error' };
					}
					try {
						const result = await api.send_host_control(
							selectedHost.value, command, param1, param2
						);
						if (result.status === 'success') {
							ElMessage.success("命令已发送");
						} else {
							ElMessage.error(result.message || "发送失败");
						}
						return result;
					} catch (error) {
						console.error("主机控制失败:", error);
						ElMessage.error("主机控制失败");
						return { status: 'error' };
					}
				};

				const toggleHostMode = async () => {
					const command = isAutoMode.value ? 'manual' : 'auto';
					const result = await sendHostControl(command);
					if (result.status === 'success') {
						isAutoMode.value = !isAutoMode.value;
					}
				};

				const setFireExtinguisher = async (index, turnOn) => {
					const command = turnOn ? 'fire_on' : 'fire_off';
					const result = await sendHostControl(command, index, 0);
					if (result.status === 'success') {
						fireExtinguisherStatus.value[index] = turnOn;
					}
				};

				const resetHost = async () => {
					await sendHostControl('reset');
				};
				// 取模拟数据部分，前端调试用
				// ========================================================================
				xhr = Vue.ref({});	
				
				/*
				// 这个是一起读的，更换成下面分开的
				const get_all_data = async () => {
					xhr = await api.get_all_hosts();
					console.log(xhr)
					

 					hostStatus.value = xhr.whole.hostStatus;
					hostProblems.value = xhr.whole.hostProblems;
					
					selectedHostInfo.value = xhr.host.selectedHostInfo;
					detectors.value = xhr.host.detectors;
					subboards.value = xhr.host.subboards;
					currentHostFaults.value = xhr.host.currentHostFaults;
					outputsStatus.value = xhr.host.outputsStatus;
					outputslockStatus.value = xhr.host.outputslockStatus;
					dcControlStatus.value = xhr.host.dcControlStatus;
					inputsStatus.value = xhr.host.inputsStatus; 
				};
				
				get_all_data();
				//*/
				
				///*
				const get_all_hosts = async () => {
					aaa = await api.get_all_hosts();
					
					// $$$$$ swgao 此处不知为何，不能直接使用函数返回，需要aaa中转
					xhr.whole = aaa;//await api.get_all_hosts();//aaa;
					//console.log(555,xhr.whole);
					
					hostStatus.value = xhr.whole.hostStatus;
					hostProblems.value = xhr.whole.hostProblems;
										
				};
				// 统一把历史记录变成 UI 需要的字段
				const Normalize_History_ForUi = (list) => {
				return (list || []).map(r => ({
					...r,
					typeText: HistoryTypeText(r),  // 你已有
					timeText: r.time ? new Date(r.time * 1000).toLocaleString() : ""
				}));
				};

				// 合并去重（按字段拼 key，你可以按实际字段调整）
				const Merge_History = (oldList, newList, maxKeep = 100) => {
				const keyOf = (r) => [
					r?.time ?? "",
					r?.type ?? "",
					r?.code ?? "",
					r?.addr ?? "",
					r?.message ?? ""
				].join("|");

				const map = new Map();
				(oldList || []).forEach(r => map.set(keyOf(r), r));
				(newList || []).forEach(r => map.set(keyOf(r), r)); // 新覆盖旧

				const merged = Array.from(map.values()).sort((a, b) => (b.time || 0) - (a.time || 0));
				return merged.slice(0, maxKeep);
				};

				const Load_LocalHistory = async (hid, limit = 200) => {
				try {
					if (!api.load_history_file) return [];
					const local = await api.load_history_file(hid, limit);
					return Array.isArray(local) ? local : [];
				} catch (e) {
					console.warn("Load_LocalHistory failed:", e);
					return [];
				}
				};

				const Save_LocalHistory = async (hid, list) => {
				try {
					if (!api.save_history_file) return;
					await api.save_history_file(hid, list);
				} catch (e) {
					console.warn("Save_LocalHistory failed:", e);
				}
				};

				// ===== 历史记录文件保存节流 =====
				let lastHistorySaveMs = 0;
				const Can_SaveHistory_Now = () => {
				const now = Date.now();
				if (now - lastHistorySaveMs < 5000) return false; // 5 秒一次
				lastHistorySaveMs = now;
				return true;
				};

				const get_host_data = async (hid) => {
					xhr.host = await api.get_host_data(hid);
					
					selectedHostInfo.value = xhr.host.selectedHostInfo;
					detectors.value = xhr.host.detectors;
					subboards.value = xhr.host.subboards;
					currentHostFaults.value = xhr.host.currentHostFaults;
					outputsStatus.value = xhr.host.outputsStatus;
					outputslockStatus.value = xhr.host.outputslockStatus;
					// 根据 outputslockStatus 的第一个值设置 isAutoMode
					isAutoMode.value = outputslockStatus.value[0];
					dcControlStatus.value = xhr.host.dcControlStatus;
					inputsStatus.value = xhr.host.inputsStatus;                    
					
					
					// ===== 新增：拉取 0x10 历史记录 =====
					// ===== 历史记录：本地缓存优先，在线更新，节流落盘 =====
					let localList = historyCache.value[hid] || [];

					// 1) 第一次进入该 hid：从本地文件读一次 + 立刻刷新 UI
					if (!historyCache.value[hid]) {
					try {
						if (api.load_history_file) {
						localList = await api.load_history_file(hid, 200);
						if (!Array.isArray(localList)) localList = [];
						} else {
						localList = [];
						}
					} catch (e) {
						console.warn("load_history_file failed:", e);
						localList = [];
					}

					historyCache.value[hid] = localList;
					currentHostHistory.value = Normalize_History_ForUi(localList);
					}

					// 2) 在线拉最新并合并（在线失败也没关系）
					try {
					const fresh = await api.get_history(hid, 50);

					const merged = Merge_History(localList, fresh, 200);
					historyCache.value[hid] = merged;

					// 用合并后的结果刷新 UI
					currentHostHistory.value = Normalize_History_ForUi(merged);

					// 3) 节流落盘（只保存一次）
					if (api.save_history_file && Can_SaveHistory_Now()) {
						await api.save_history_file(hid, merged);
					}
					} catch (e) {
					console.warn("get_history failed:", e);
					// 保持显示本地缓存即可
					}

				};
				get_all_hosts();
				// get_host_data(1);

				// 添加定时刷新函数（打包 exe 长期运行：降低轮询频率，减轻 CPU/接口压力）
				const UI_REFRESH_MS = 1000;
				const startAutoRefresh = () => {
					if (updateTimer.value) {
						clearInterval(updateTimer.value);
					}
					updateTimer.value = setInterval(() => {
						get_all_hosts();
					}, UI_REFRESH_MS);
				};
				const startAutoRefresh1 = (hid) => {
					if (updateTimer.value) {
						clearInterval(updateTimer.value);
						updateTimer.value = null;
					}
					updateTimer.value = setInterval(() => {
						get_host_data(hid);
					}, UI_REFRESH_MS);
				};

				// 判断当前是否在详情页面
				const isDetailPage = window.location.pathname.includes('detail.html');
				
				// 如果是详情页面，从URL获取主机ID并初始化数据
				if (isDetailPage) {
					const params = new URLSearchParams(window.location.search);
					const hostname = params.get('hostname');
					if (!hostname) {
						console.error("detail.html 缺少 hostname 参数");
						ElementPlus.ElMessage.error("缺少主机参数，请从主页进入");
					} else {
					const hostId = parseInt(hostname.replace(/[^0-9]/g, ''));
					
					// 设置当前选中的主机ID
					selectedHost.value = hostId;
					console.log("详情页面初始化，主机ID:", hostId);
					
					// 初始化数据
					get_host_data(hostId);
					
					// 启动定时刷新
					Vue.onMounted(() => {
						startAutoRefresh1(hostId);
					});
					}
				} else {
					// 在主页面启动常规刷新
					Vue.onMounted(() => {
						getConnectionStatus();

					});
				}

				// 确保在组件卸载时清除定时器
				Vue.onUnmounted(() => {
					if (updateTimer.value) {
						clearInterval(updateTimer.value);
						updateTimer.value = null;
					}
				});
				
				// ========================================================================
				
				// ========================================================================
				// 页面切换逻辑
				// 进入主机详情页面
				const viewProblemDetails = (problem) => {
					// 标记问题为已查看
					viewedProblems.value.add(problem.hostname + problem.problem);
					problem.viewed = true;
					
					// 从主机名中提取数字
					const hostNumber = problem.hostname.replace(/[^0-9]/g, '');

					// enterHost();
				};
				
		
				// 页面的切换
				// 新增监听 currentPage 变化，在切换到 hostSelect/hostControl 时更新数据
				Vue.watch(currentPage, async (newPage) => {
					
					/*
					// 切换到不同的页面
					if (newPage === 'hostSelect') {
						try {
							updateHostProblems();
						} catch (error) {
							ElMessage.error("加载主机状态失败");
						}
					}
					
					if (newPage === 'hostControl') {
						try {
							// 这里可以添加从后端获取探测器和故障数据的逻辑
							// const response = await api.get_host_data(selectedHost.value);
							// detectors.value = response.detectors;
							// faults.value = response.faults;
						} catch (error) {
							ElMessage.error("加载主机数据失败");
						}
					}
					*/
				});
				
				///*

				// 返回主机选择页面
				const backToHostSelect = () => {
					if (updateTimer.value) {
						clearInterval(updateTimer.value);
						updateTimer.value = null;
					}
					//currentPage.value = 'hostSelect';
					currentPage.value = 'hostSelect';
					window.location.href = `./index.html`;									
				};					
				// 进入主机
				const enterHost = async (item) => {
					if (!item || !item.hostname) {
						console.error("enterHost: 缺少必要的参数");
						return;
					}
					
					// 获取最新连接状态
					await getConnectionStatus();
					
					// 从主机名中提取ID
					const hostId = parseInt(item.hostname.replace(/[^0-9]/g, ''));
					selectedHost.value = hostId;
					console.log("开始启动主机数据定时器, 主机ID:", hostId);
					
					// 跳转到详情页面
					window.location.href = `./detail.html?hostname=${item.hostname}`;
				};		
				//*/
					
				// ========================================================================


				// 在 setup() 函数中添加一个新的响应式变量用于存储定时器ID
				

				// 在组件卸载时清除定时器
				Vue.onUnmounted(() => {
					if (updateTimer.value) {
						clearInterval(updateTimer.value);
						updateTimer.value = null;
					}
				});

				const handOpen=()=>{
					dialogVisible.value=true
				}			
				
				// 在 setup() 中添加获取连接状态的函数
				const getConnectionStatus = async () => {
					try {
						const status = await api.get_connection_status();
						console.log("【getConnectionStatus】后端返回：", status);
						isConnected.value = !!status.is_connected;
						selectedPort.value = status.pcan_info?.Channel || status.pcan_info?.Device_name || null;
					} catch (error) {
						console.error("获取连接状态失败:", error);
					}
				};

				// 暴露给模板, 当数据变化时，Vue 会自动更新相关视图
				return {
					//以下是变量或结构体
					currentPage,			//各个子页面切换
					getStatusColor,			//主机信息列表的颜色（区分报警不报警）
					viewProblemDetails,		//报警是否已被查看
					
					
					
					//放到一个里面不就完了
					//xhr.whole
					hostStatus,				//主机子设备信息列表结构体
					hostProblems,			//主机报警信息列表结构体->hostStatus->get_mainboard_status
		
		
					//xhr.host
					selectedHostInfo,		//当前激活的主机结构体->hostStatus->get_mainboard_status					
					detectors,				//探测器结构体->getDetectorData
					subboards,				//分区探测子控制器结构体->get_subboard_status
					currentHostFaults,		//主机当前的故障结构体->faults->get_detector_status
					outputsStatus,			//自动模式时，主机当前警报输出状态
					//outputslockStatus,	//			
					dcControlStatus,		//手动模式时，主机要进行开关控制
					inputsStatus,			//主机报警输入结构体


					//智能选择某种颜色
					getProblemTextColor,	//报警信息颜色函数
					getRowClassName,
					
					
					//串口相关
					serialPorts,
					selectedPort,
					isConnected,
					searchSerialPorts,
					connectSerialPort,
					disconnectSerialPort,
					toggleConnect,
					//页面切换函数
					enterHost,
					backToHostSelect,

					dialogVisible,
					handOpen,
					controlPanelVisible,
					getFireStatusText,
					toggleHostMode,
					setFireExtinguisher,
					resetHost,

					isAutoMode,				//手动、自动变量
					handleDCControl,		//主机输出控制函数
					currentHostHistory,	 		// 主机历史记录
					/*					
					hostAutoModeMap,		//主机8个警报输出状态记录
					isAutoMode,				//手动、自动变量
					
					//以下是函数
					handleDCControl,		//主机输出控制函数
					updateHostData,			//刷新主机数据函数
										
					updateTimer,			//页面刷新函数
					toggleControlMode,		//手动、自动模式切换函数					
					
					onlineHosts,	
					selectedHost,
					searchHosts,
					searchSerialPorts,

					noteTitle,
					noteContent,		

					faults,
					*/
					//=================
				};
			}
			
		});

		app.use(ElementPlus, {
			locale: ElementPlusLocaleZhCn
		});

		app.mount('#app');
}

window.addEventListener("pywebviewready", bootApp);

// 打包 exe：由 pywebview 注入 API；仅 file:// 本地浏览器调试才加载 mock
function isBrowserDebugMode() {
	return window.location.protocol === "file:";
}

setTimeout(function () {
	if (appStarted) return;
	if (typeof pywebview !== "undefined" && pywebview.api) {
		bootApp();
		return;
	}
	if (!isBrowserDebugMode()) {
		console.log("等待 pywebview API 注入...");
		return;
	}
	var script = document.createElement("script");
	script.src = "browser-api.js";
	script.onload = bootApp;
	document.head.appendChild(script);
}, 300);