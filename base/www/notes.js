				// 加载笔记
				const loadNotes = async () => {
					try {
						const notes = await api.get_notes();
						noteTitle.value = notes.title;
						noteContent.value = notes.content;
					} catch (error) {
						console.error("加载笔记失败:", error);
					}
				};

				// 保存笔记
				const saveNotes = async () => {
					try {
						const result = await api.save_notes(noteTitle.value, noteContent.value);
						if (result.status === 'success') {
							ElMessage.success("保存成功");
						} else {
							ElMessage.error("保存失败: " + result.message);
						}
					} catch (error) {
						console.error("保存笔记失败:", error);
						ElMessage.error("保存失败");
					}
				};

				// 监听笔记变化自动保存
				Vue.watch([noteTitle, noteContent], () => {
					saveNotes();
				});

				// 初始加载笔记
				loadNotes();
				
				// 初始搜索串口
				searchSerialPorts();