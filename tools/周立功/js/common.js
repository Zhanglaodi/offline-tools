let Tools = {
    /**
     * 数据处理
     * @param data
     * @param requests_data
     * @date 2022年8月10日08:15:30
     * @returns {*}
     */
    data_parse: (data, requests_data) => {
        // 判断数据是否存在
        if (!data) {
            return layer.msg('数据不存在,请检查数据')
        }
        // 逐条数据解析
        return data.map((row) => {
            return [
                row['time'], Tools._data_parsing(row, requests_data)
            ]
        });
    },

    /**
     * 数据解析
     * @param row
     * @param requests_data
     * @returns {number}
     * @date 2022年8月10日08:15:12
     * @private
     */
    _data_parsing: (row, requests_data) => {
        // 判断数据类型
        let tmp_data = '';
        if (requests_data['interest'] === 'intel') {
            row['data'].reverse();
            for (let res_row of row['data']) {
                tmp_data += parseInt(res_row, 16).toString(2).padStart(8, '0')
            }
            row['data'].reverse();
            tmp_data = tmp_data.split('').reverse().join('')
            tmp_data = tmp_data.substring(parseInt(requests_data['start']), parseInt(requests_data['start']) + parseInt(requests_data['len']))
            tmp_data = tmp_data.split('').reverse().join('')
        } else if (requests_data['interest'] === 'motorola') {
            // motorola
            for (let res_row of row['data']) {
                tmp_data += parseInt(res_row, 16).toString(2).padStart(8, '0')
            }
            let res = parseInt((parseInt(requests_data['start']) + 1) / 8) * 8 + (8 - ((parseInt(requests_data['start']) + 1) % 8))
            tmp_data = tmp_data.substring(res - parseInt(requests_data['len']) + 1, res + 1)
        } else {
            for (let res_row of row['data']) {
                tmp_data += parseInt(res_row, 16).toString(2).padStart(8, '0')
            }
            let res = parseInt((parseInt(requests_data['start'])) / 8) * 8 + (8 - ((parseInt(requests_data['start'])) % 8))
            tmp_data = tmp_data.substring(res - 1, res + parseInt(requests_data['len']) - 1)
        }

        if (requests_data['data_type'] === 'unsigned') {
            tmp_data = parseInt(tmp_data, 2)
        } else {
            if (tmp_data.substring(0, 1) === '1') {
                let max_tmp_data = Array(tmp_data.length).fill(1).join('').slice(-tmp_data.length)
                tmp_data = -(parseInt(max_tmp_data, 2) - parseInt(tmp_data, 2) + 1)
            } else {
                tmp_data = parseInt(tmp_data, 2)
            }
        }
        return (tmp_data * parseFloat(requests_data['accuracy'])) - parseFloat(requests_data['offset']);
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