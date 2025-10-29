let Tools = {
    /**
     * 数据处理 - 内存优化版本
     * @param data
     * @param requests_data
     * @date 2022年8月10日08:15:30
     * @returns {*}
     */
    data_parse: (data, requests_data) => {
        // 判断数据是否存在
        if (!data || !Array.isArray(data)) {
            return layer.msg('数据不存在或格式错误,请检查数据')
        }
        
        // 检查数据量，大数据量使用不同策略
        if (data.length > 50000) {
            console.warn(`数据量较大(${data.length}条)，建议使用流式处理`);
        }
        
        // 使用更高效的数组预分配
        const result = new Array(data.length);
        
        // 批量处理，减少内存压力
        const BATCH_SIZE = 2000; // 减小批次大小
        let resultIndex = 0;
        
        for (let i = 0; i < data.length; i += BATCH_SIZE) {
            const end = Math.min(i + BATCH_SIZE, data.length);
            
            // 处理当前批次
            for (let j = i; j < end; j++) {
                const row = data[j];
                if (row && row.time !== undefined) {
                    try {
                        const value = Tools._data_parsing(row, requests_data);
                        result[resultIndex++] = [parseFloat(row.time), value];
                    } catch (error) {
                        console.warn(`处理第${j}条数据时出错:`, error.message);
                        // 跳过错误数据，继续处理
                    }
                }
            }
            
            // 每处理一定数量后检查内存
            if (i % (BATCH_SIZE * 5) === 0 && performance.memory) {
                const used = performance.memory.usedJSHeapSize;
                const limit = performance.memory.jsHeapSizeLimit;
                if (used / limit > 0.8) {
                    console.warn('内存使用率过高，暂停处理');
                    if (window.gc) window.gc();
                }
            }
        }
        
        // 截断结果数组到实际大小
        result.length = resultIndex;
        return result;
    },

    /**
     * 流式数据处理 - 适用于大数据量
     * @param data
     * @param requests_data
     * @param onProgress 进度回调函数
     * @returns {Promise}
     */
    data_parse_stream: async (data, requests_data, onProgress) => {
        if (!data) {
            throw new Error('数据不存在,请检查数据');
        }
        
        const result = [];
        const BATCH_SIZE = 500; // 减小批次大小，提高响应性
        const total = data.length;
        
        for (let i = 0; i < total; i += BATCH_SIZE) {
            const end = Math.min(i + BATCH_SIZE, total);
            
            // 处理当前批次
            for (let j = i; j < end; j++) {
                const row = data[j];
                result.push([
                    parseFloat(row['time']), 
                    Tools._data_parsing(row, requests_data)
                ]);
            }
            
            // 更新进度
            if (onProgress) {
                const progress = Math.round((end / total) * 100);
                onProgress(progress);
            }
            
            // 让出控制权，避免阻塞UI
            await new Promise(resolve => setTimeout(resolve, 0));
        }
        
        return result;
    },

    /**
     * 数据解析 - 优化版本，减少字符串操作
     * @param row
     * @param requests_data
     * @returns {number}
     * @date 2022年8月10日08:15:12
     * @private
     */
    _data_parsing: (row, requests_data) => {
        const start = parseInt(requests_data['start']);
        const len = parseInt(requests_data['len']);
        const accuracy = parseFloat(requests_data['accuracy']);
        const offset = parseFloat(requests_data['offset']);
        const interest = requests_data['interest'];
        const dataType = requests_data['data_type'];
        
        let tmp_data = '';
        const rowData = row['data'];
        
        if (interest === 'intel') {
            // 反向处理intel格式
            for (let i = rowData.length - 1; i >= 0; i--) {
                tmp_data += parseInt(rowData[i], 16).toString(2).padStart(8, '0');
            }
            tmp_data = tmp_data.substring(start, start + len);
            // 反转结果
            tmp_data = tmp_data.split('').reverse().join('');
        } else if (interest === 'motorola') {
            // motorola格式处理
            for (let i = 0; i < rowData.length; i++) {
                tmp_data += parseInt(rowData[i], 16).toString(2).padStart(8, '0');
            }
            const res = Math.floor((start + 1) / 8) * 8 + (8 - ((start + 1) % 8));
            tmp_data = tmp_data.substring(res - len + 1, res + 1);
        } else {
            // 五菱格式处理
            for (let i = 0; i < rowData.length; i++) {
                tmp_data += parseInt(rowData[i], 16).toString(2).padStart(8, '0');
            }
            const res = Math.floor(start / 8) * 8 + (8 - (start % 8));
            tmp_data = tmp_data.substring(res - 1, res + len - 1);
        }

        // 数据类型转换
        let value;
        if (dataType === 'unsigned') {
            value = parseInt(tmp_data, 2);
        } else {
            if (tmp_data.charAt(0) === '1') {
                const maxValue = (1 << tmp_data.length) - 1;
                value = -(maxValue - parseInt(tmp_data, 2) + 1);
            } else {
                value = parseInt(tmp_data, 2);
            }
        }
        
        return (value * accuracy) - offset;
    },

    /**
     * 内存使用监控和管理
     */
    getMemoryUsage: () => {
        if (performance.memory) {
            const used = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
            const total = Math.round(performance.memory.totalJSHeapSize / 1024 / 1024);
            const limit = Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024);
            const usagePercent = (used / limit * 100).toFixed(1);
            
            return {
                used: used + ' MB',
                total: total + ' MB', 
                limit: limit + ' MB',
                usagePercent: usagePercent + '%',
                isHigh: used / limit > 0.7,
                isCritical: used / limit > 0.85
            };
        }
        return null;
    },

    /**
     * 强制垃圾回收（如果支持）
     */
    forceGarbageCollection: () => {
        if (window.gc) {
            console.log('执行强制垃圾回收');
            window.gc();
            return true;
        } else {
            console.warn('浏览器不支持手动垃圾回收');
            return false;
        }
    },

    /**
     * 内存清理建议
     */
    getMemoryOptimizationTips: () => {
        const memory = Tools.getMemoryUsage();
        if (!memory) return ['无法获取内存信息'];
        
        const tips = [];
        if (memory.isCritical) {
            tips.push('⚠️ 内存使用率过高，建议：');
            tips.push('1. 关闭其他浏览器标签页');
            tips.push('2. 刷新页面释放内存');
            tips.push('3. 使用更小的文件进行处理');
        } else if (memory.isHigh) {
            tips.push('⚡ 内存使用率较高，建议：');
            tips.push('1. 避免同时处理多个文件');
            tips.push('2. 定期刷新页面');
        } else {
            tips.push('✅ 内存使用正常');
        }
        
        return tips;
    },

    // 生成excel，data为传入数据，name为生成的文件名称
    data_export: (data) => {
        let csv_name = new Set();
        //encodeURIComponent解决中文乱码
        let uri = "data:text/csv;charset=utf-8,\ufeff" + encodeURIComponent(Object.keys(data).map((can_id) => {
            // 获取全部的表头数据
            let curve_name_keys = Object.keys(data[can_id]).filter((value, index, array) => {
                return value !== 'row';
            });
            let table_header = ['时间', 'CAN_ID', ...curve_name_keys];
            // 补充表头数据
            let table_content = table_header.join(',') + '\n';
            // 获取曲线数据
            let _tmp_swp = [];
            for (const _tmp_data of data[can_id]['row']) {
                _tmp_swp = [];
                _tmp_swp.push(_tmp_data['time']);
                _tmp_swp.push(_tmp_data['can_id']);
                for (const curve_name of curve_name_keys) {
                    csv_name.add(curve_name);
                    _tmp_swp.push(Tools._data_parsing(_tmp_data, data[can_id][curve_name]['requests_data']));
                }
                table_content += _tmp_swp.join(',') + '\n';
            }
            return table_content;
        }).join('\n\n\n'));
        //通过创建a标签实现
        let link = document.createElement("a");
        link.href = uri;
        //对下载的文件命名
        link.download = Array.from(csv_name).join(' - ') + ".csv";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

};