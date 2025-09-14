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

};