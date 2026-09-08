// 直接启html页面的效果
// 模拟 pywebview.api 接口
window.pywebview = {
    api: {
        // 模拟搜索串口
        search_serial_ports: async function() {
            console.log('浏览器模式：模拟搜索串口');
            return {
                'COM1': '模拟串口1',
                'COM2': '模拟串口2'
            };
        },
        
        // 模拟连接串口
        connect_serial_port: async function() {
            console.log('浏览器模式：模拟连接串口');
            return { status: 'Connected' };
        },
        
        // 模拟断开连接
        disconnect_serial_port: async function() {
            console.log('浏览器模式：模拟断开串口');
            return { status: 'Disconnected' };
        },
        
        // 模拟发送数据
        send_data: async function(data) {
            console.log('浏览器模式：模拟发送数据', data);
            return { status: 'Success' };
        },
        
        // 模拟获取所有数据
		get_all_hosts: async function() {
			
			xhr = {};
			
			//整体全部主机列表页面虚拟数据
			xhr.whole = {};
			
			
			xhr.whole.hostStatus = [{},{}];
			xhr.whole.hostStatus[0].hostname = '主机2';
			xhr.whole.hostStatus[0].status = '正常';
			xhr.whole.hostStatus[0].sensorCount = 1;			
			xhr.whole.hostStatus[0].faultCount = 3;
			xhr.whole.hostStatus[0].alertCount = 2;
			xhr.whole.hostStatus[0].alertLevel = 1;	
			
			xhr.whole.hostStatus[1].hostname = '主机3';
			xhr.whole.hostStatus[1].status = '火警';
			xhr.whole.hostStatus[1].sensorCount = 1;			
			xhr.whole.hostStatus[1].faultCount = 3;
			xhr.whole.hostStatus[1].alertCount = 2;
			xhr.whole.hostStatus[1].alertLevel = 1;					


			xhr.whole.hostProblems = [{}];
			xhr.whole.hostProblems[0].hostname = '主机1';
			xhr.whole.hostProblems[0].problem = '火警';

			console.log(111,xhr.whole);

			return xhr.whole;
		},
		
		get_host_data: async function(hid) {
			
			xhr = {};
			
			//某个特定主机数据
			xhr.host = {};
			
			xhr.host.selectedHostInfo = [{}];
			xhr.host.selectedHostInfo[0].onlineSensors = 3;
			xhr.host.selectedHostInfo[0].problemCount = 2;
			xhr.host.selectedHostInfo[0].alertLevel = 1;			
			
			xhr.host.detectors = [{}];
			xhr.host.detectors[0].name = '探测器1';
			xhr.host.detectors[0].signal = '10%';
			xhr.host.detectors[0].temperature = 0;
			xhr.host.detectors[0].co = 0.1;
			xhr.host.detectors[0].smoke = 2;
			xhr.host.detectors[0].voc = 3;
			xhr.host.detectors[0].hydrogen = 55;

			


			xhr.host.subboards = [{}];
			xhr.host.subboards[0] = {};
			xhr.host.subboards[0].id = '子板1';
			xhr.host.subboards[0].signalStrength = 80;				
			xhr.host.subboards[0].outputs = [1,0];
			xhr.host.subboards[0].inputs = [1,0,1];
			
			xhr.host.currentHostFaults = [{}];
			xhr.host.currentHostFaults[0] = {};
			xhr.host.currentHostFaults[0].name = '探测器2';
			xhr.host.currentHostFaults[0].description = '警报级别1';		

			xhr.host.outputsStatus = [1,0,0,1,1,0,0,1];
			xhr.host.dcControlStatus = [1,0,0,1,1,0,0,1];
			xhr.host.inputsStatus = [1,0,0,1,1,0,0,1];	

			return xhr.host;
		},
		
        get_all_data: async function() {
			
			xhr = {};
			
			
			//整体全部主机列表页面虚拟数据
			xhr.whole = {};
			
			
			xhr.whole.hostStatus = [{},{}];
			xhr.whole.hostStatus[0].hostname = '主机2';
			xhr.whole.hostStatus[0].status = '正常';
			xhr.whole.hostStatus[0].sensorCount = 1;			
			xhr.whole.hostStatus[0].faultCount = 3;
			xhr.whole.hostStatus[0].alertCount = 2;
			xhr.whole.hostStatus[0].alertLevel = 1;	
			
			xhr.whole.hostStatus[1].hostname = '主机3';
			xhr.whole.hostStatus[1].status = '火警';
			xhr.whole.hostStatus[1].sensorCount = 1;			
			xhr.whole.hostStatus[1].faultCount = 3;
			xhr.whole.hostStatus[1].alertCount = 2;
			xhr.whole.hostStatus[1].alertLevel = 1;					


			xhr.whole.hostProblems = [{}];
			xhr.whole.hostProblems[0].hostname = '主机1';
			xhr.whole.hostProblems[0].problem = '火警';
			
			
			//某个特定主机数据
			xhr.host = {};
			
			xhr.host.selectedHostInfo = [{}];
			xhr.host.selectedHostInfo[0].onlineSensors = 3;
			xhr.host.selectedHostInfo[0].problemCount = 2;
			xhr.host.selectedHostInfo[0].alertLevel = 1;			
			
			xhr.host.detectors = [{}];
			xhr.host.detectors[0].name = '探测器1';
			xhr.host.detectors[0].signal = '10%';
			xhr.host.detectors[0].temperature = 0;
			xhr.host.detectors[0].co = 0.1;
			xhr.host.detectors[0].smoke = 2;
			xhr.host.detectors[0].voc = 3;
			xhr.host.detectors[0].hydrogen = 55;
			xhr.host.detectors[0].name = '探测器1';
			xhr.host.detectors[0].signal = '10%';
			xhr.host.detectors[0].temperature = 0;
			xhr.host.detectors[0].co = 0.1;
			xhr.host.detectors[0].smoke = 2;
			xhr.host.detectors[0].voc = 3;
			xhr.host.detectors[0].hydrogen = 55;				
			
			xhr.host.subboards = [{}];
			xhr.host.subboards[0] = {};
			xhr.host.subboards[0].id = '子板1';
			xhr.host.subboards[0].signalStrength = 80;				
			xhr.host.subboards[0].outputs = [1,0];
			xhr.host.subboards[0].inputs = [1,0,1];
			
			xhr.host.currentHostFaults = [{}];
			xhr.host.currentHostFaults[0] = {};
			xhr.host.currentHostFaults[0].name = '探测器2';
			xhr.host.currentHostFaults[0].description = '警报级别1';		

			xhr.host.outputsStatus = [1,0,0,1,1,0,0,1];
			xhr.host.dcControlStatus = [1,0,0,1,1,0,0,1];
			xhr.host.inputsStatus = [1,0,0,1,1,0,0,1];
					
			
            return xhr;
        },
        
        // 模拟日志操作
        log_action: async function(message) {
            console.log('浏览器模式:', message);
            return { status: 'Success' };
        },

        send_host_control: async function(hostid, command, param1 = 0, param2 = 0) {
            console.log('浏览器模式：主机控制', { hostid, command, param1, param2 });
            return { status: 'success' };
        },

        control_dc: async function(hostid, switch_number, status) {
            console.log('浏览器模式：control_dc', { hostid, switch_number, status });
            return { status: 'success' };
        },

        get_connection_status: async function() {
            return { is_connected: false, pcan_info: {} };
        }
    }
}; 