// XT Static Server (Go version, optional build to .exe)
// Build (Windows x64):
//   1) Install Go (https://go.dev/dl/)
//   2) go build -ldflags "-s -w" -o server.exe server.go
// Usage:
//   server.exe                # uses server_config.json
//   server.exe 0.0.0.0 8080  # override host/port
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"mime"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type Config struct {
	Port        int    `json:"port"`
	Host        string `json:"host"`
	OpenBrowser bool   `json:"open_browser"`
	RootDir     string `json:"root_dir"`
}

func readConfig() Config {
	cfg := Config{Port: 8080, Host: "127.0.0.1", OpenBrowser: true, RootDir: "."}
	b, err := os.ReadFile("server_config.json")
	if err == nil {
		var c Config
		if json.Unmarshal(b, &c) == nil {
			if c.Port != 0 { cfg.Port = c.Port }
			if c.Host != "" { cfg.Host = c.Host }
			cfg.OpenBrowser = c.OpenBrowser
			if c.RootDir != "" { cfg.RootDir = c.RootDir }
		}
	}
	return cfg
}

func openBrowser(url string) {
	cmd := exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	_ = cmd.Start()
}

func main() {
	cfg := readConfig()
	if len(os.Args) == 3 {
		cfg.Host = os.Args[1]
		fmt.Sscanf(os.Args[2], "%d", &cfg.Port)
	} else if len(os.Args) == 2 {
		fmt.Sscanf(os.Args[1], "%d", &cfg.Port)
	}
	root, err := filepath.Abs(cfg.RootDir)
	if err != nil {
		log.Fatal(err)
	}

	// ensure some mime types
	_ = mime.AddExtensionType(".js", "application/javascript; charset=utf-8")
	_ = mime.AddExtensionType(".json", "application/json; charset=utf-8")
	_ = mime.AddExtensionType(".css", "text/css; charset=utf-8")
	_ = mime.AddExtensionType(".html", "text/html; charset=utf-8")

	fs := http.FileServer(http.Dir(root))
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// CORS for convenience
		w.Header().Set("Access-Control-Allow-Origin", "*")
		// security: prevent path traversal is handled by FileServer, but we can log
		log.Printf("%s %s %s", r.RemoteAddr, r.Method, r.URL.Path)
		// default file for root
		if r.URL.Path == "/" {
			if _, err := os.Stat(filepath.Join(root, "index.html")); err != nil {
				w.Header().Set("Content-Type", "text/html; charset=utf-8")
				fmt.Fprintf(w, "<h1>XT Static Server</h1><pre>Root: %s\nURL : http://%s:%d/</pre>", root, cfg.Host, cfg.Port)
				return
			}
		}
		fs.ServeHTTP(w, r)
	})

	addr := net.JoinHostPort(cfg.Host, fmt.Sprintf("%d", cfg.Port))
	srv := &http.Server{
		Addr:              addr,
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
	}

	fmt.Printf("XT Static Server started at http://%s:%d (root: %s)\n", cfg.Host, cfg.Port, root)
	if cfg.OpenBrowser {
		go func() {
			time.Sleep(400 * time.Millisecond)
			openBrowser(fmt.Sprintf("http://%s:%d", cfg.Host, cfg.Port))
		}()
	}
	if err := srv.ListenAndServe(); err != nil && !strings.Contains(err.Error(), "closed") {
		log.Fatal(err)
	}
}
