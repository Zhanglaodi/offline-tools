// Web Worker 用于处理大文件数据
// 避免阻塞主线程

self.onmessage = function(e) {
    const { type, data } = e.data;
    
    try {
        switch (type) {
            case 'PARSE_FILE_CHUNK':
                handleFileChunk(data);
                break;
            case 'PARSE_DATA':
                handleDataParsing(data);
                break;
            default:
                self.postMessage({ type: 'ERROR', error: '未知的操作类型' });
        }
    } catch (error) {
        self.postMessage({ 
            type: 'ERROR', 
            error: error.message,
            stack: error.stack 
        });
    }
};

// 处理文件块
function handleFileChunk(data) {
    const { chunk, isVersion7, first_time, chunkIndex } = data;
    const lines = chunk.split('\n');
    
    let result = {
        file_context: {},
        can_id: [],
        first_time: first_time
    };
    
    if (isVersion7) {
        result = processChunkVersion7(lines, first_time, chunkIndex === 0);
    } else {
        result = processChunkVersionOld(lines, first_time, chunkIndex === 0);
    }
    
    self.postMessage({
        type: 'CHUNK_PROCESSED',
        data: {
            chunkIndex,
            ...result
        }
    });
}

// 处理数据解析
function handleDataParsing(data) {
    const { sourceData, requests_data, batchSize = 1000 } = data;
    const total = sourceData.length;
    const result = [];
    
    // 批量处理
    for (let i = 0; i < total; i += batchSize) {
        const end = Math.min(i + batchSize, total);
        
        for (let j = i; j < end; j++) {
            const row = sourceData[j];
            const value = dataParsing(row, requests_data);
            result.push([parseFloat(row.time), value]);
        }
        
        // 发送进度更新
        const progress = Math.round((end / total) * 100);
        self.postMessage({
            type: 'PROGRESS',
            data: { progress }
        });
    }
    
    self.postMessage({
        type: 'DATA_PARSED',
        data: { result }
    });
}

// 版本7.0.0的数据块处理
function processChunkVersion7(lines, first_time, isFirstChunk) {
    const skipLines = isFirstChunk ? 3 : 0;
    const file_context = {};
    const can_id = [];
    
    for (let i = skipLines; i < lines.length; i++) {
        const row = lines[i];
        if (row.length > 5) {
            const parts = row.split(' ');
            if (parts.length > 5) {
                if (first_time === null) {
                    first_time = parseFloat(parts[0]);
                }
                const t_rel = (parseFloat(parts[0]) - first_time).toFixed(6);
                const canId = parts[2];
                
                can_id.push(canId);
                file_context[canId] = file_context[canId] || [];
                file_context[canId].push({
                    'can_id': canId,
                    'time': t_rel,
                    'data': parts.slice(6, 14)
                });
            }
        }
    }
    
    return { file_context, can_id, first_time };
}

// 旧版本的数据块处理
function processChunkVersionOld(lines, first_time, isFirstChunk) {
    const skipLines = isFirstChunk ? 2 : 0;
    const file_context = {};
    const can_id = [];
    
    for (let i = skipLines; i < lines.length; i++) {
        const row = lines[i];
        if (row.length > 5) {
            const parts = row.split(' ');
            if (parts.length > 5) {
                parts[0] = parts[0].replace('\t1', '');
                if (first_time === -1) {
                    first_time = parseFloat(parts[0]);
                }
                const t_rel = (parseFloat(parts[0]) - first_time).toFixed(6);
                
                const can_id_list = parts[1].split('\t');
                const _can_id = can_id_list[0];
                
                can_id.push(_can_id);
                file_context[_can_id] = file_context[_can_id] || [];
                file_context[_can_id].push({
                    'can_id': _can_id,
                    'time': t_rel,
                    'data': [can_id_list[can_id_list.length - 1], ...parts.slice(2, 9)]
                });
            }
        }
    }
    
    return { file_context, can_id, first_time };
}

// 数据解析函数（从common.js复制的逻辑）
function dataParsing(row, requests_data) {
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
}