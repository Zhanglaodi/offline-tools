XT Static Server · 绿色本地静态服务

文件说明
- start_server.bat   双击即可启动（内部调用 server.ps1）
- server.ps1         PowerShell 版本静态服务器，零依赖
- server_config.json 配置文件（端口/主机/根目录/是否自动打开浏览器）
- server.go          （可选）Go 源码，自己编译成 server.exe

使用方式（零依赖方案）
1) 将本包与 index.html / data.json 放在同一目录
2) 双击 start_server.bat
3) 浏览器将自动打开 http://127.0.0.1:8080

可选：修改 server_config.json
{
    "port": 8080,
    "host": "0.0.0.0",
    "open_browser": true,
    "root_dir": "."
}

可选：编译成 server.exe（需要安装 Go）
  go build -ldflags "-s -w" -o server.exe server.go
